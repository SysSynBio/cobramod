#!/usr/bin/env python3
"""Unittest for module graph

In this modules, the new algorithm is tested. The TestCase GraphTesting checks
that the behavior of all important functions works as intended
"""
from itertools import chain
from logging import DEBUG
from pathlib import Path
from unittest import TestCase, main

from cobra import __version__

from cobramod.debug import debug_log
from cobramod.error import GraphKeyError
from cobramod.test import textbook_kegg
import cobramod.core.graph as gr
from cobramod import __version__ as cobramod_version

# Debug must be set in level DEBUG for the test
debug_log.setLevel(DEBUG)
# Setting directory for data
dir_data = Path(__file__).resolve().parent.joinpath("data")
# If data is missing, then do not test. Data should always be the same
if not dir_data.exists():
    raise NotADirectoryError("Data for the test is missing")

print(f"CobraMod version: {cobramod_version}")
print(f"COBRApy version: {__version__}")


class GraphTesting(TestCase):
    """
    This new TestCase Checks that the behavior of the new algorithm works as
    intended.
    """

    def test_find_missing(self):
        # CASE 1: Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        gr.find_missing(graph=test_dict)
        # CASE 1b: Simple Lineal, Error
        test_dict = {"R1": ("R2", "R4"), "R2": "R3", "R3": None}
        self.assertRaises(GraphKeyError, gr.find_missing, graph=test_dict)

    def test_find_cycle(self):
        # CASE 1: Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_answer = gr.find_cycle(graph=test_dict, key="R1", visited=[])
        self.assertIs(expr1=False, expr2=test_answer)
        # CASE 1b: Simple Lineal, Error
        test_dict = {"R1": ("R2", "R4"), "R2": "R3", "R3": None}
        self.assertRaises(
            GraphKeyError, gr.find_cycle, graph=test_dict, key="R1", visited=[]
        )
        # CASE 2: cyclic
        test_dict = {"R1": "R2", "R2": "R3", "R3": "R1"}
        test_answer = gr.find_cycle(graph=test_dict, key="R1", visited=[])
        self.assertCountEqual(first=["R1", "R2", "R3"], second=test_answer)
        # CASE 2a: Complex Lineal / Missing Key
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R5": None,
        }
        self.assertRaises(
            GraphKeyError, gr.find_cycle, graph=test_dict, key="R0", visited=[]
        )
        # CASE 2a: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": None,
            "R5": None,
        }
        test_answer = gr.find_cycle(graph=test_dict, key="R0", visited=[])
        self.assertIs(expr1=False, expr2=test_answer)
        # CASE 3: Complex Cyclic
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R0",
            "R5": None,
        }
        test_answer = gr.find_cycle(graph=test_dict, key="R0", visited=[])
        self.assertCountEqual(
            first=["R0", "R1", "R2", "R3", "R4"], second=test_answer
        )
        # CASE 4: Complex full Cycle
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R0",
            "R5": "R4",
        }
        # Behavior of tuples
        test_answer = gr.find_cycle(graph=test_dict, key="R1", visited=[])
        self.assertEqual(first=len(test_answer), second=4)

    def test_return_cycles(self):
        # CASE 1: Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_list = gr.return_cycles(graph=test_dict)
        self.assertFalse(expr=test_list)
        # CASE 1: Complex Cyclic
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R0",
            "R5": None,
        }
        test_list = gr.return_cycles(graph=test_dict)
        self.assertIn(
            member=["R0", "R1", "R2", "R3", "R4"], container=test_list
        )
        # CASE 2: Graph with cycle, from Biocyc (GLUCONEO-PWY)
        test_dict = {
            "R1": "R13",
            "R2": "R3",
            "R3": ("R2", "R1"),
            "R4": None,
            "R5": "R4",
            "R6": "R5",
            "R7": "R6",
            "R8": "R7",
            "R9": "R8",
            "R10": None,
            "R11": "R10",
            "R12": None,
            "R13": None,
        }
        test_list = gr.return_cycles(graph=test_dict)
        self.assertIn(member=["R3", "R2"], container=test_list)
        # CASE 3: Complex Cycle (CALVIN-PWY)
        test_dict = {
            "R1": ("R11", "R2"),
            "R2": "R10",
            "R3": "R2",
            "R4": "R7",
            "R5": "R4",
            "R6": "R5",
            "R7": ("R8", "R13"),
            "R8": "R9",
            "R9": "R1",
            "R10": "R6",
            "R11": None,
            "R12": "R3",
            "R13": "R12",
        }
        test_list = gr.return_cycles(graph=test_dict)
        # pass

    def test_cut_cycle(self):
        # CASE 1: Simple cut
        test_dict = {"R1": "R2", "R2": "R3", "R3": "R1"}
        gr.cut_cycle(graph=test_dict, key="R1")
        self.assertDictEqual(
            d1=test_dict, d2={"R1": None, "R2": "R3", "R3": "R1"}
        )

    def test_back(self):
        # CASE 1: Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_answer = gr.back(graph=test_dict, value="R3", path=[])
        self.assertListEqual(list1=test_answer, list2=["R1", "R2"])
        # CASE 2: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": None,
            "R5": None,
        }
        # For R5
        test_answer = gr.back(graph=test_dict, value="R5", path=[])
        self.assertListEqual(list1=test_answer, list2=["R0", "R1"])
        # For R4
        test_answer = gr.back(graph=test_dict, value="R4", path=[])
        self.assertListEqual(list1=test_answer, list2=["R0", "R1", "R2", "R3"])
        # CASE 3a: Rest with stop list
        test_dict = {
            "R7": ("R8", "R11"),
            "R8": "R10",
            "R9": None,
            "R10": None,
            "R11": None,
        }
        test_answer = gr.back(
            graph=test_dict,
            value="R10",
            path=[],
            stop_list=["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R12"],
        )
        self.assertListEqual(list1=test_answer, list2=["R7", "R8"])
        # CASE 3b: Rest with stop list. Single element
        test_answer = gr.back(
            graph=test_dict,
            value="R9",
            path=[],
            stop_list=["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R12"],
        )
        self.assertListEqual(list1=test_answer, list2=[])

    def test_verify_paths(self):
        # CASE 1: Complex Cycle (after modification)
        test_dict = {"R1": ("R11", "R2"), "R2": None, "R3": "R2", "R11": None}
        test_list = [["R1", "R2"]]
        test_answer = gr.verify_paths(paths=test_list, graph=test_dict)
        self.assertCountEqual(first=test_answer, second=["R3", "R11"])

    def test_get_paths(self):
        # CASE 0: Unrelated
        test_dict = {"R1": None, "R2": None, "R3": None}
        test_list = gr.get_paths(graph=test_dict, stop_list=[])
        self.assertEqual(first=len(test_list), second=3)
        self.assertIn(member=["R1"], container=test_list)
        self.assertIn(member=["R2"], container=test_list)
        self.assertIn(member=["R3"], container=test_list)
        # CASE 1: Simple Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_list = gr.get_paths(graph=test_dict, stop_list=[])
        self.assertListEqual(
            list1=["R1", "R2", "R3"], list2=max(test_list, key=len)
        )
        # CASE 2a: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": None,
            "R5": None,
        }
        test_list = gr.get_paths(graph=test_dict, stop_list=[])
        self.assertListEqual(
            list1=["R0", "R1", "R2", "R3", "R4"], list2=max(test_list, key=len)
        )
        # CASE 2b: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R7"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R5",
            "R5": ("R6", "R9"),
            "R6": "R12",
            "R7": ("R8", "R11"),
            "R8": "R10",
            "R9": None,
            "R10": None,
            "R11": None,
            "R12": None,
        }
        test_list = gr.get_paths(graph=test_dict, stop_list=[])
        self.assertEqual(first=len(test_list), second=4)
        self.assertListEqual(
            list1=["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R12"],
            list2=max(test_list, key=len),
        )
        # CASE 3: Using Rest
        test_dict = {
            "R7": ("R8", "R11"),
            "R8": "R10",
            "R9": None,
            "R10": None,
            "R11": None,
        }
        stop_list = (["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R12"],)
        test_list = gr.get_paths(graph=test_dict, stop_list=stop_list)
        self.assertEqual(first=len(test_list), second=3)
        self.assertListEqual(
            list1=["R7", "R8", "R10"], list2=max(test_list, key=len)
        )
        # CASE 4: Complex Cycle (after modification)
        test_dict = {
            "R1": ("R11", "R2"),
            "R2": None,
            "R3": "R2",
            "R4": "R7",
            "R5": "R4",
            "R6": "R5",
            "R7": ("R8", "R13"),
            "R8": "R9",
            "R9": "R1",
            "R10": "R6",
            "R11": None,
            "R12": "R3",
            "R13": "R12",
        }
        test_list = gr.get_paths(graph=test_dict, stop_list=stop_list)
        # TODO: due to temporal fix, list is now 5 instead of 3
        self.assertEqual(first=len(test_list), second=5)

    def test_get_mapping(self):
        # CASE 0a: Single element
        test_dict = {"R1": None}
        test_list = gr.get_mapping(graph=test_dict, stop_list=[], new=[])
        self.assertListEqual(list1=test_list, list2=[["R1"]])
        # CASE 0b: Unrelated
        test_dict = {"R1": None, "R2": None, "R3": None}
        test_list = gr.get_mapping(graph=test_dict, stop_list=[], new=[])
        self.assertIn(member=["R1"], container=test_list)
        self.assertIn(member=["R2"], container=test_list)
        self.assertIn(member=["R3"], container=test_list)
        # CASE 1: Simple Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_list = gr.get_mapping(graph=test_dict, stop_list=[], new=[])
        self.assertListEqual(list1=test_list, list2=[["R1", "R2", "R3"]])
        # CASE 2: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": None,
            "R5": None,
        }
        test_list = gr.get_mapping(graph=test_dict, stop_list=[], new=[])
        self.assertListEqual(
            list1=test_list[0], list2=["R0", "R1", "R2", "R3", "R4"]
        )
        self.assertListEqual(list1=test_list[1], list2=["R5"])
        # CASE 2b: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R7"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R5",
            "R5": ("R6", "R9"),
            "R6": "R12",
            "R7": ("R8", "R11"),
            "R8": "R10",
            "R9": None,
            "R10": None,
            "R11": None,
            "R12": None,
        }
        test_list = gr.get_mapping(graph=test_dict, stop_list=[], new=[])
        # Test the two longest maps
        self.assertListEqual(
            list1=test_list[0],
            list2=["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R12"],
        )
        self.assertListEqual(list1=test_list[1], list2=["R7", "R8", "R10"])

    def test_build_graph(self):
        # CASE 0: Single Element
        test_dict = {"R1": None}
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=1)
        self.assertListEqual(list1=test_list[0], list2=["R1"])
        # CASE 0b: Unrelated
        test_dict = {"R1": None, "R2": None, "R3": None}
        test_list = gr.build_graph(graph=test_dict)
        self.assertIn(member=["R1"], container=test_list)
        self.assertIn(member=["R2"], container=test_list)
        self.assertIn(member=["R3"], container=test_list)
        # CASE 1: Simple Lineal
        test_dict = {"R1": "R2", "R2": "R3", "R3": None}
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=1)
        # CASE 1b: Simple Lineal, Error
        test_dict = {"R1": ("R2", "R4"), "R2": "R3", "R3": None}
        self.assertRaises(GraphKeyError, gr.build_graph, graph=test_dict)
        # CASE 2: Simple Cyclic
        test_dict = {"R1": "R2", "R2": "R3", "R3": "R1"}
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=1)
        # CASE 3: Complex Lineal
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R7"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R5",
            "R5": ("R6", "R9"),
            "R6": "R12",
            "R7": "R8",
            "R8": ("R10", "R11"),
            "R9": None,
            "R10": None,
            "R11": None,
            "R12": None,
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=4)
        self.assertIn(member=["R11"], container=test_list)
        # CASE 3: Complex Cyclic
        test_dict = {
            "R0": "R1",
            "R1": ("R2", "R5"),
            "R2": "R3",
            "R3": "R4",
            "R4": "R0",
            "R5": None,
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=2)
        # CASE 4: Complex Lineal
        test_dict = {
            "R1": "R2",
            "R2": ("R3", "R5", "R4"),
            "R3": ("R6", "R8"),
            "R4": None,
            "R5": None,
            "R6": "R7",
            "R7": "R10",
            "R8": ("R9", "R11"),
            "R9": None,
            "R10": "R14",
            "R11": ("R12", "R13"),
            "R12": None,
            "R13": None,
            "R14": None,
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=6)
        # CASE 5: Module from KEGG
        test_dict = {
            "R0": "R3",
            "R1": "R3",
            "R2": "R3",
            "R3": ("R4", "R5"),
            "R4": "R6",
            "R5": "R6",
            "R6": "R7",
            "R7": ("R8", "R9"),
            "R8": "R10",
            "R9": "R10",
            "R10": "R11",
            "R11": "R12",
            "R12": "R13",
            "R13": "R14",
            "R14": None,
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=5)
        # CASE 6: Cyclic with inside cycle
        test_dict = {
            "R1": "R13",
            "R2": "R3",
            "R3": ("R2", "R1"),
            "R4": None,
            "R5": "R4",
            "R6": "R5",
            "R7": "R6",
            "R8": "R7",
            "R9": "R8",
            "R10": None,
            "R11": "R10",
            "R12": None,
            "R13": None,
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(first=len(test_list), second=5)
        # CASE 7: Complex cyclic
        test_dict = {
            "R1": ("R11", "R2"),
            "R2": "R10",
            "R3": "R2",
            "R4": "R7",
            "R5": "R4",
            "R6": "R5",
            "R7": ("R8", "R13"),
            "R8": "R9",
            "R9": "R1",
            "R10": "R6",
            "R11": "R10",
            "R12": "R3",
            "R13": "R12",
        }
        test_list = gr.build_graph(graph=test_dict)
        self.assertEqual(
            first=len(set(chain.from_iterable(test_list))), second=13
        )

    def test__format_graph(self):
        # CASE 1: Under other name
        test_model = textbook_kegg.copy()
        test_dict = {"ACALD": "MALS", "MALS": None}
        test_graph = gr._format_graph(
            graph=test_dict,
            model=test_model,
            compartment="c",
            directory=dir_data,
            model_id="e_coli_core",
            database="BIGG",
            avoid_list=[],
            replacement={},
            genome=None,
        )
        self.assertEqual(first=test_graph["R00228_c"], second="R00472_c")
        self.assertEqual(first=test_graph["R00472_c"], second=None)
        self.assertEqual(first=len(test_graph), second=2)
        # CASE 2: Avoid list
        test_model = textbook_kegg.copy()
        test_dict = {"ACALD": "MALS", "MALS": None}
        test_graph = gr._format_graph(
            graph=test_dict,
            model=test_model,
            compartment="c",
            directory=dir_data,
            model_id="universal",
            database="BIGG",
            avoid_list=["ACALD"],
            replacement={},
            genome=None,
        )
        self.assertEqual(first=test_graph["R00472_c"], second=None)
        self.assertEqual(first=len(test_graph), second=1)
        # CASE 3: Replacement
        test_model = textbook_kegg.copy()
        # ACALDt have to be changed to ACALDt_c
        test_model.reactions.get_by_id("ACALDt").id = "ACALDt_c"
        test_dict = {"ACALD": "MALS", "MALS": None}
        test_graph = gr._format_graph(
            graph=test_dict,
            model=test_model,
            compartment="c",
            directory=dir_data,
            model_id="universal",
            database="BIGG",
            avoid_list=[],
            replacement={"ACALD": "ACALDt"},
            genome=None,
        )
        self.assertEqual(first=test_graph["ACALDt_c"], second="R00472_c")
        self.assertEqual(first=test_graph["R00472_c"], second=None)
        self.assertEqual(first=len(test_graph), second=2)

    def test__fix_graph(self):
        graph = {
            "RXN-11430": ("RXN-19589", "RXN-11438"),
            "RXN-19589": "RXN-8052",
            "RXN-8052": "RXN-2208",
            "RXN-2223": ("RXN-11445", "RXN-2224"),
            "RXN-11438": "RXN-2208",
            "RXN-11422": "RXN-11430",
            "RXN-11414": "RXN-11422",
            "RXN-2206": "RXN-11414",
            "RXN-2221": ("RXN-2223", "RXN-2222"),
            "RXN-2209": "RXN-2221",
            "RXN-2208": "RXN-2209",
            "RXN-11445": None,
            "RXN-2222": None,
            "RXN-2224": None,
        }
        # CASE 0: No difference
        test_graph = gr._fix_graph(graph=graph.copy(), avoid_list=[])
        self.assertDictEqual(d1=graph, d2=test_graph)

        # CASE 1: Using avoid_list
        new_graph = {
            "RXN-11430": "RXN-19589",
            "RXN-19589": "RXN-8052",
            "RXN-8052": "RXN-2208",
            "RXN-11422": "RXN-11430",
            "RXN-2221": None,
            "RXN-2209": "RXN-2221",
            "RXN-2208": "RXN-2209",
        }
        test_graph = gr._fix_graph(
            graph=graph.copy(),
            avoid_list=[
                "RXN-2206",
                "RXN-11414",
                "RXN-11438",
                "RXN-2222",
                "RXN-2223",
                "RXN-2224",
                "RXN-11445",
            ],
        )
        self.assertDictEqual(d1=new_graph, d2=test_graph)


if __name__ == "__main__":
    main(verbosity=2)
