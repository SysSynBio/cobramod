#!/usr/bin/env python3
"""Unit-test for model behavior

This module checks if a large and a small model behaves as intended. This
examples should simulate real cases. There are two test:

- ShortModel: This should utilize the textbook_biocyc model from cobramod.
- LargeModel: Uses a real GEM
"""
from logging import DEBUG
from pathlib import Path
from unittest import TestCase, main

from cobra.io import read_sbml_model

from cobramod.core import extension as ex
from cobramod.core.creation import add_reactions
from cobramod.debug import debug_log
from cobramod.test import textbook_biocyc

# Debug must be set in level DEBUG for the test
debug_log.setLevel(DEBUG)
# Setting directory for data
dir_data = Path(__file__).resolve().parent.joinpath("data")
dir_input = Path(__file__).resolve().parent.joinpath("input")

# If data is missing, then do not test. Data should always be the same
if not dir_data.exists():
    raise NotADirectoryError("Data for the test is missing")

# Large Model
main_model = read_sbml_model(str(dir_input.joinpath("test_model.sbml")))


if not dir_data.exists():
    dir_data.mkdir(parents=True)


class ShortModel(TestCase):
    def test_lineal_pathways(self):
        # For this test, Gluconeogenesis; L-aspartate and L-asparagine
        # biosynthesis, and Nicotine biosynthesis added to test for feasible
        # results.
        test_model = textbook_biocyc.copy()

        # Adding Gluconeogenesis
        ex.add_pathway(
            model=test_model,
            pathway="GLUCONEO-PWY",
            directory=dir_data,
            database="META",
            compartment="c",
            show_imbalance=False,
        )
        self.assertGreater(a=abs(test_model.optimize().objective_value), b=0)
        self.assertIn(
            member="GLUCONEO-PWY",
            container=[group.id for group in test_model.groups],
        )
        add_reactions(
            model=test_model,
            obj=(
                "Redox_Hemoprotein_c, Redox_Hemoprotein_c | "
                + "Ox-NADPH-Hemoprotein-Reductases_c <-> "
                + "Red-NADPH-Hemoprotein-Reductases_c"
            ),
            directory=dir_data,
            database="ARA",
        )

        # Adding Nicotine pathway
        ex.add_pathway(
            model=test_model,
            pathway="PWY-5316",
            directory=dir_data,
            database="META",
            compartment="c",
            ignore_list=[],
            show_imbalance=False,
        )
        self.assertIn(
            member="PWY-5316",
            container=[group.id for group in test_model.groups],
        )

        # Ading aspartate and asparagine biosynthesis
        ex.add_pathway(
            model=test_model,
            pathway="ASPASN-PWY",
            directory=dir_data,
            database="META",
            compartment="c",
            ignore_list=[],
            show_imbalance=False,
        )
        self.assertGreater(a=abs(test_model.optimize().objective_value), b=0)
        self.assertIn(
            member="ASPASN-PWY",
            container=[group.id for group in test_model.groups],
        )

    def test_cyclical_pathways(self):
        test_model = textbook_biocyc.copy()

        # Adding Mannitol cycle
        ex.add_pathway(
            model=test_model,
            pathway="PWY-6531",
            directory=dir_data,
            database="META",
            compartment="c",
            ignore_list=[],
            show_imbalance=False,
        )
        self.assertIn(
            member="PWY-6531",
            container=[group.id for group in test_model.groups],
        )

        # Adding glyoxylate cycle
        ex.add_pathway(
            model=test_model,
            pathway="GLYOXYLATE-BYPASS",
            directory=dir_data,
            database="ARA",
            compartment="c",
            ignore_list=[],
            show_imbalance=False,
        )
        self.assertGreater(a=abs(test_model.optimize().objective_value), b=0)
        self.assertIn(
            member="GLYOXYLATE-BYPASS",
            container=[group.id for group in test_model.groups],
        )

    def test_multi_compartment(self):
        test_model = textbook_biocyc.copy()
        # This files has transports between cytosol and plastids
        add_reactions(
            model=test_model,
            obj=dir_input.joinpath("test_multi_reactions.txt"),
            database="ARA",
            directory=dir_data,
        )

        ex.add_pathway(
            model=test_model,
            pathway="GLUTATHIONESYN-PWY",
            directory=dir_data,
            database="ARA",
            ignore_list=[],
            compartment="p",
            show_imbalance=False,
        )
        test_model.reactions.get_by_id("Biomass_Ecoli_core").add_metabolites(
            {test_model.metabolites.get_by_id("GLUTATHIONE_p"): -1}
        )

        self.assertIn(
            member="GLUTATHIONESYN-PWY",
            container=[group.id for group in test_model.groups],
        )

        self.assertGreater(abs(test_model.optimize().objective_value), 0)

        add_reactions(
            model=test_model,
            obj="TRANS_GLY_cp, Transport GLY_cp | GLY_c <-> GLY_p",
            directory=dir_data,
            database="ARA",
        )

        ex.add_pathway(
            model=test_model,
            pathway="PWY-1187",
            directory=dir_data,
            database="ARA",
            ignore_list=["PYRUVATE_c", "CO_A_c", "PROTON_c", "CPD_3746_c"],
            compartment="c",
            show_imbalance=False,
        )

        test_model.reactions.get_by_id("Biomass_Ecoli_core").add_metabolites(
            {
                test_model.metabolites.get_by_id(
                    "3_METHYLSULFINYLPROPYL_GLUCOSINOLATE_c"
                ): -0.75,
                test_model.metabolites.get_by_id("GLUTATHIONE_p"): 1,
            }
        )
        self.assertGreater(abs(test_model.optimize().objective_value), 0)

        # Lipid initalization
        ex.add_pathway(
            model=test_model,
            pathway="PWY-4381",
            directory=dir_data,
            database="ARA",
            ignore_list=["CO_A_p"],
            compartment="p",
            show_imbalance=False,
        )
        test_model.reactions.get_by_id("Biomass_Ecoli_core").add_metabolites(
            {test_model.metabolites.get_by_id("Acetoacetyl_ACPs_p"): -1}
        )

        self.assertGreater(test_model.slim_optimize(error_value=0), 0)


class LargeModel(TestCase):
    def test_lineal_pathways(self):
        """In this test, unrelated pathways are appended to the large model
        and tested
        """
        test_model = main_model.copy()

        # Autotroph environment
        test_model.reactions.Sucrose_tx.bounds = (0, 0)  # SUCROSE
        test_model.reactions.GLC_tx.bounds = (0, 0)  # GLUCOSE

        # # Photon uptake
        test_model.reactions.Photon_tx.bounds = (-1000, 250)

        # No ammonium
        test_model.reactions.NH4_tx.bounds = (0, 0)
        test_model.objective = "Biomass_tx"

        # Adding methionine metabolism
        ex.add_pathway(
            model=test_model,
            pathway="PWY-7614",
            directory=dir_data,
            database="META",
            compartment="p",
            show_imbalance=False,
        )

        # Optimizing methiin
        test_model.objective = "RXN_8908_p"

        self.assertGreater(test_model.optimize().fluxes["RXN_16201_p"], 0)
        self.assertGreater(test_model.slim_optimize(error_value=0), 0)

        # Adding stachyose biosynthesis
        test_model.objective = "Biomass_tx"

        ex.add_pathway(
            model=test_model,
            pathway="PWY-5337",
            directory=dir_data,
            database="ARA",
            compartment="c",
            show_imbalance=False,
        )

        # Optimizing raffinose
        test_model.objective = "2.4.1.82_RXN_c"

        self.assertGreater(test_model.optimize().fluxes["2.4.1.123_RXN_c"], 0)
        self.assertGreater(test_model.slim_optimize(error_value=0), 0)

        # Adding abscisic acid
        test_model.objective = "Biomass_tx"

        ex.add_pathway(
            model=test_model,
            pathway="PWY-695",
            directory=dir_data,
            database="ARA",
            compartment="p",
            show_imbalance=False,
        )

        # Optimizing abscisate
        test_model.objective = "1.2.3.14_RXN_p"

        self.assertGreater(test_model.optimize().fluxes["1.1.1.288_RXN_p"], 0)
        self.assertGreater(test_model.slim_optimize(error_value=0), 0)

        test_model.objective = "Biomass_tx"
        self.assertGreater(test_model.slim_optimize(error_value=0), 0)


if __name__ == "__main__":
    main(verbosity=2)
