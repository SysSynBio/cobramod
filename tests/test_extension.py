#!/usr/bin/env python3
"""Unittest for module extension

this module test the behavior of multiple functions, which are responsible to
add metabolites and reactions into a metabolic model. This module can be
divided in to parts:

- CreatingSequences: Functions, that create the corresponding reactions as
sequences and their corresponding flux test.
- AddingPathways: Functions, that manage the addition of Pathways into the
metabolic models.
"""
from logging import DEBUG
from pathlib import Path
from unittest import main, TestCase

from cobra import Model, Reaction

from cobramod.core import extension as ex
from cobramod.core.creation import add_reactions, get_data
from cobramod.core.pathway import Pathway
from cobramod.debug import debug_log
from cobramod.error import UnbalancedReaction
from cobramod.test import textbook_biocyc, textbook_kegg, textbook


# Debug must be set in level DEBUG for the test
debug_log.setLevel(DEBUG)
# Setting directory for data
dir_data = Path(__file__).resolve().parent.joinpath("data")
dir_input = Path(__file__).resolve().parent.joinpath("input")
# If data is missing, then do not test. Data should always be the same
if not dir_data.exists():
    raise NotADirectoryError("Data for the test is missing")


class CreatingSequences(TestCase):
    """
    Test for simpler functions
    """

    def test__create_reactions(self):
        # CASE 1: Simple Case Biocyc
        test_list = ex._create_reactions(
            sequence=[
                "OXALODECARB-RXN",
                "AROMATIC-L-AMINO-ACID-DECARBOXYLASE-RXN",
            ],
            compartment="c",
            directory=dir_data,
            database="ARA",
            replacement={},
            show_imbalance=False,
            stop_imbalance=False,
            model=Model(0),
            model_id="",
            genome=None,
        )
        self.assertIsInstance(obj=next(test_list), cls=Reaction)
        # CASE 2: Simple case Kegg
        test_list = ex._create_reactions(
            sequence=["R00200", "R00114"],
            compartment="p",
            directory=dir_data,
            database="KEGG",
            replacement={},
            show_imbalance=False,
            stop_imbalance=False,
            model=Model(0),
            model_id="",
            genome="eco",
        )
        self.assertIsInstance(obj=next(test_list), cls=Reaction)
        # CASE 3a: Showing when unbalanced
        test_list = ex._create_reactions(
            sequence=["RXN-2206", "RXN-11414", "RXN-11422"],
            compartment="c",
            directory=dir_data,
            database="ARA",
            replacement={},
            show_imbalance=True,
            stop_imbalance=False,
            model=Model(0),
            model_id="",
            genome=None,
        )
        self.assertWarns(UserWarning, next, test_list)
        # CASE 3b: Stopping when unbalanced
        test_list = ex._create_reactions(
            sequence=["RXN-2206", "RXN-11414", "RXN-11422"],
            compartment="c",
            directory=dir_data,
            database="ARA",
            show_imbalance=False,
            stop_imbalance=True,
            replacement={},
            model=Model(0),
            model_id="",
            genome=None,
        )
        self.assertRaises(UnbalancedReaction, next, test_list)

    def test_test_non_zero_flux(self):
        # CASE 1: Single Regular reaction
        test_model = Model(0)

        add_reactions(
            model=test_model,
            obj="RXN-2206, c",
            directory=dir_data,
            database="ARA",
            replacement={},
            show_imbalance=False,
        )
        ex.test_non_zero_flux(model=test_model, reaction="RXN_2206_c")
        self.assertEqual(first=7, second=len(test_model.sinks))

        # CASE 0: minimun range not reached
        # INFO: this extra steps are needed in order to make it fail
        test_model = textbook_biocyc.copy()
        add_reactions(
            model=test_model,
            obj=[
                "Redox_ADP_ATP_p, Redox_ADP_ATP_p | ADP_p <-> ATP_p",
                "TRANS_Pi_cp, Transport Phosphate_cp | Pi_c <-> Pi_p",
                "TRANS_GLUTATHIONE_cp, Transport GLUTATHIONE_cp |"
                + " GLUTATHIONE_c <-> GLUTATHIONE_p",
                "GLUTATHIONE-SYN-RXN, p",
            ],
            database="ARA",
            directory=dir_data,
            show_imbalance=False,
        )
        self.assertWarns(
            UserWarning,
            ex.test_non_zero_flux,
            model=test_model,
            reaction="GLUTATHIONE_SYN_RXN_p",
        )

        # CASE 2: direction right to left
        test_model = Model(0)
        add_reactions(
            model=test_model,
            obj="1.8.4.9-RXN, c",
            directory=dir_data,
            database="ARA",
        )
        ex.test_non_zero_flux(model=test_model, reaction="1.8.4.9_RXN_c")
        self.assertEqual(first=6, second=len(test_model.sinks))


class AddingPathways(TestCase):
    """
    Test for functions related to the addition of Pathways and their
    visualizations.
    """

    def test__add_sequence(self):
        # CASE 1: Normal usage (3 reactions)
        test_model = textbook_biocyc.copy()
        test_list = list(
            ex._create_reactions(
                sequence=["RXN-2206", "RXN-11414", "RXN-11422"],
                compartment="c",
                directory=dir_data,
                database="ARA",
                replacement={},
                show_imbalance=False,
                stop_imbalance=False,
                model=test_model,
                model_id="",
                genome=None,
            )
        )
        ex._add_sequence(
            model=test_model,
            pathway=Pathway("test_group"),
            sequence=test_list,
            ignore_list=["WATER_c", "OXYGEN_MOLECULE_c"],
        )
        self.assertGreater(
            abs(test_model.slim_optimize(error_value=0)), 0  # type: ignore
        )
        self.assertIn(
            member="test_group",
            container=[group.id for group in test_model.groups],
        )
        # CASE 2: reactions already in model
        test_model = textbook.copy()
        reactions = [
            reaction
            for reaction in test_model.reactions
            if reaction.id in ("GAPD", "PGK", "PGM")
        ]
        ex._add_sequence(
            model=test_model,
            pathway=Pathway("test_group"),
            sequence=reactions,
            ignore_list=[],
        )
        self.assertIn(
            member="test_group",
            container=[group.id for group in test_model.groups],
        )
        self.assertEqual(
            first=len(test_model.groups.get_by_id("test_group")), second=3
        )
        # CASE 3: KEGG
        test_model = textbook_kegg.copy()
        test_list = list(
            ex._create_reactions(
                sequence=["R00894", "R00497"],
                compartment="c",
                directory=dir_data,
                database="KEGG",
                replacement={},
                show_imbalance=False,
                stop_imbalance=False,
                model=test_model,
                model_id="",
                genome="ath",
            )
        )
        ex._add_sequence(
            model=test_model,
            pathway=Pathway("test_group_kegg"),
            sequence=test_list,
            ignore_list=["WATER_c", "OXYGEN_MOLECULE_c"],
        )
        self.assertGreater(
            abs(test_model.slim_optimize(error_value=0)), 0  # type: ignore
        )
        self.assertIn(
            member="test_group_kegg",
            container=[group.id for group in test_model.groups],
        )

    def test__from_data(self):
        test_dict = get_data(
            identifier="M00118",
            directory=dir_data,
            debug_level=10,
            database="KEGG",
        )
        # CASE 1: regular test with KEGG
        test_model = textbook_kegg.copy()
        ex._from_data(
            model=test_model,
            group=None,
            data_dict=test_dict,
            directory=dir_data,
            database="KEGG",
            compartment="c",
            avoid_list=[],
            replacement={},
            ignore_list=[],
            show_imbalance=False,
            stop_imbalance=False,
            model_id="",
            genome="hsa",
        )
        self.assertIn(
            member="M00118",
            container=[group.id for group in test_model.groups],
        )
        for item in ["2729", "2937"]:
            self.assertIn(
                member=item, container=[gene.id for gene in test_model.genes]
            )
        # CASE 2: Using another label
        test_model = textbook_kegg.copy()
        ex._from_data(
            model=test_model,
            data_dict=test_dict,
            directory=dir_data,
            database="KEGG",
            group="ALTERNATIVE",
            compartment="c",
            avoid_list=[],
            replacement={},
            ignore_list=[],
            show_imbalance=False,
            stop_imbalance=False,
            model_id="",
            genome="hsa",
        )
        self.assertIn(
            member="ALTERNATIVE",
            container=[group.id for group in test_model.groups],
        )

    def test__from_sequence(self):
        # CASE 1: regular test
        test_model = textbook_biocyc.copy()
        ex._from_sequence(
            model=test_model,
            identifier="test_group",
            compartment="c",
            sequence=["R01063", "R09084"],
            database="KEGG",
            directory=dir_data,
            avoid_list=[],
            replacement={},
            ignore_list=[],
            show_imbalance=False,
            stop_imbalance=False,
            model_id="",
            genome="mba",
        )
        self.assertIn(
            member="test_group",
            container=[group.id for group in test_model.groups],
        )
        for item in ["Mbar_A2189", "Mbar_A3564"]:
            self.assertIn(
                member=item, container=[gene.id for gene in test_model.genes]
            )

    def test__from_strings(self):
        test_model = Model(0)
        test_list = [
            "RXN-14462, c",
            "ACETALD-DEHYDROG-RXN ,c",
            "AMONITRO-RXN, c",
        ]

        ex._from_strings(
            model=test_model,
            obj=test_list,
            replacement={"Not_GLC": "GLC"},
            pathway_name="test_group",
            show_imbalance=False,
            stop_imbalance=False,
            model_id="",
            database="GCF_000020025",
            directory=dir_data,
            ignore_list=[],
            genome=None,
        )
        for reaction in (
            "RXN_14462_c",
            "ACETALD_DEHYDROG_RXN_c",
            "AMONITRO_RXN_c",
        ):
            self.assertIn(
                member=reaction,
                container=[reaction.id for reaction in test_model.reactions],
            )

    def test_add_pathway(self):
        # CASE 1: Regular Biocyc
        test_model = textbook_biocyc.copy()
        ex.add_pathway(
            model=test_model,
            pathway="PWY-1187",
            compartment="c",
            directory=dir_data,
            database="ARA",
            ignore_list=[],
            show_imbalance=False,
        )
        self.assertIn(
            member="RXN_11438_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        for item in ["AT1G18590", "AT1G74090"]:
            self.assertIn(
                member=item, container=[gene.id for gene in test_model.genes]
            )
        # CASE 2: stacking another pathways (independent from each other)
        ex.add_pathway(
            model=test_model,
            pathway="AMMOXID-PWY",
            compartment="c",
            directory=dir_data,
            database="META",
            show_imbalance=False,
        )
        self.assertGreater(
            abs(test_model.slim_optimize(error_value=0)), 0  # type: ignore
        )
        sol = test_model.optimize()
        # Test for demands, all should have a flux
        for demand in test_model.demands:
            self.assertGreater(a=abs(sol.fluxes[demand.id]), b=0)
        self.assertEqual(first=len(test_model.groups), second=2)
        # CASE 3: using a simple sequence
        test_model = textbook_biocyc.copy()
        test_sequence = ["RXN-2206", "RXN-11414", "RXN-11422", "RXN-11430"]
        ex.add_pathway(
            model=test_model,
            compartment="c",
            pathway=test_sequence,
            ignore_list=[],
            database="ARA",
            directory=dir_data,
            show_imbalance=False,
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        self.assertIn(
            member="RXN_11422_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        # CASE 3a: Behavior if reaction was already in model
        test_model = textbook_biocyc.copy()
        # Adding reactions
        test_sequence = ["RXN-2206", "RXN-11414"]
        ex.add_pathway(
            model=test_model,
            group="old_reactions",
            compartment="c",
            pathway=test_sequence,
            ignore_list=[],
            database="META",
            directory=dir_data,
            show_imbalance=False,
        )
        test_sequence = ["RXN-2206", "RXN-11414", "RXN-11422", "RXN-11430"]
        ex.add_pathway(
            model=test_model,
            compartment="c",
            pathway=test_sequence,
            ignore_list=[],
            database="ARA",
            directory=dir_data,
            show_imbalance=False,
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        test_group = test_model.groups.get_by_id("custom_group")
        for identifier in ["RXN_2206_c", "RXN_11414_c", "RXN_11422_c"]:
            self.assertIn(
                member=identifier,
                container=[reaction.id for reaction in test_group.members],
            )
        # CASE 4a: KEGG simple pathway
        test_model = textbook_kegg.copy()
        ex.add_pathway(
            model=test_model,
            pathway="M00118",
            database="KEGG",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
            genome="hsa",
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        self.assertIn(
            member="R00894_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        # CASE 4b: KEGG lineal coplex pathway
        test_model = textbook_kegg.copy()
        ex.add_pathway(
            model=test_model,
            pathway="M00001",
            database="KEGG",
            directory=dir_data,
            compartment="c",
            # This reaction has problem
            ignore_list=["C00008_c", "R09084_c"],
            avoid_list=[""],
            show_imbalance=False,
            genome="hsa",
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        self.assertIn(
            member="R01063_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        self.assertIn(
            member="R09084_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        # CASE 5a: Check for translations in pathways
        # Note VCHO does not exist in biocyc anymore
        test_model = textbook_kegg.copy()
        ex.add_pathway(
            model=test_model,
            pathway="SALVADEHYPOX-PWY",
            database="VCHO",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        test_reaction = test_model.reactions.get_by_id("ADENODEAMIN_RXN_c")
        self.assertIn(
            member="C00080_c",
            container=[
                metabolite.id for metabolite in test_reaction.metabolites
            ],
        )
        # CASE 5b: From sequence. Skipping already in Model. Stacking in one.
        test_model = textbook_kegg.copy()
        ex.add_pathway(
            model=test_model,
            pathway=["ACALD", "MALS"],
            database="BIGG",
            model_id="e_coli_core",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
            ignore_list=["R00228_c", "R00472_c"],
        )

        # Note VCHO does not exist in biocyc anymore
        ex.add_pathway(
            model=test_model,
            pathway=["ADENODEAMIN-RXN"],
            database="VCHO",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
        )
        test_reaction = test_model.reactions.get_by_id("ADENODEAMIN_RXN_c")
        # Total of one reactions
        self.assertEqual(
            first=len(test_model.groups.get_by_id("custom_group").members),
            second=3,
        )
        self.assertGreater(a=test_model.slim_optimize(), b=0)
        self.assertNotIn(
            member="ACALD_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        self.assertNotIn(
            member="MALS_c",
            container=[reaction.id for reaction in test_model.reactions],
        )
        # WATER
        self.assertIn(
            member="C00001_c",
            container=[
                metabolite.id for metabolite in test_reaction.metabolites
            ],
        )
        # CASE 5b: Testing avoid list
        test_model = textbook_kegg.copy()
        test_sequence = ["RXN-2206", "RXN-11414", "RXN-11422", "RXN-11430"]
        ex.add_pathway(
            model=test_model,
            pathway=test_sequence,
            database="ARA",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
            avoid_list=["RXN-2206"],
        )
        test_group = test_model.groups.get_by_id("custom_group")
        self.assertEqual(first=len(test_group.members), second=3)
        self.assertEqual(first=len(test_group.graph), second=3)
        # CASE 6: Stacking pathways in one pathways
        test_sequence = ["RXN-11438", "RXN-2208", "RXN-2209", "RXN-2221"]
        ex.add_pathway(
            model=test_model,
            pathway=test_sequence,
            database="ARA",
            directory=dir_data,
            compartment="c",
            show_imbalance=False,
        )
        test_group = test_model.groups.get_by_id("custom_group")
        self.assertEqual(first=len(test_group.members), second=7)
        self.assertEqual(first=len(test_group.graph), second=7)

        # CASE 7a: Using replacement arguments to rename
        test_model = textbook_biocyc.copy()
        test_replacement = {
            "RXN-8052": "Reaction_8052",
            "RXN-2208": "Reaction_2208",
            "RXN-2223": "Reaction_2223",
        }
        ex.add_pathway(
            model=test_model,
            pathway="PWY-1187",
            compartment="c",
            directory=dir_data,
            database="ARA",
            replacement=test_replacement,
            show_imbalance=False,
        )
        for meta in test_replacement.values():
            identifier = f"{meta}_c"
            self.assertIn(
                member=identifier,
                container=[reaction.id for reaction in test_model.reactions],
            )
            self.assertIn(
                member=identifier,
                container=[
                    reaction.id
                    for reaction in test_model.groups.get_by_id(
                        "PWY-1187"
                    ).members
                ],
            )

        # CASE 7b: Using replacement arguments to replace
        test_model = textbook_biocyc.copy()
        test_sequence = ["RXN-2206", "RXN-11414", "RXN-11422", "RXN-11430"]

        ex.add_pathway(
            model=test_model,
            compartment="c",
            pathway=test_sequence,
            ignore_list=[],
            database="ARA",
            directory=dir_data,
            replacement={"RXN-2206": "ACALDt"},
            show_imbalance=False,
        )

        self.assertIn(
            member="ACALDt",
            container=[
                reaction.id
                for reaction in test_model.groups.get_by_id(
                    "custom_group"
                ).members
            ],
        )
        # CASE 7b: Using replacement arguments to replace
        test_model = textbook_biocyc.copy()
        test_list = [
            "GLT_cb, Glutamate Transport| GLT_c <-> GLT_b",
            "RXN_17742_c, RXN_17742_c |"
            + "1 Oxidized-ferredoxins_c <-> 1 Reduced-ferredoxins_c ",
            "ACALDt",
        ]

        ex.add_pathway(
            model=test_model,
            compartment="c",
            pathway=test_list,
            ignore_list=[],
            directory=dir_data,
            show_imbalance=False,
        )

        for reaction in ("GLT_cb", "RXN_17742_c", "ACALDt"):
            self.assertIn(
                member=reaction,
                container=[
                    reaction.id
                    for reaction in test_model.groups.get_by_id(
                        "custom_group"
                    ).members
                ],
            )


if __name__ == "__main__":
    main(verbosity=2)
