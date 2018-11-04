# -*- coding: utf-8 -*-
#
# This file is part of Export Layers.
#
# Copyright (C) 2013-2018 khalim19 <khalim19@gmail.com>
#
# Export Layers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Export Layers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Export Layers.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *

import mock
import unittest

from gimp import pdb
import gimpenums

from export_layers import pygimplib
from export_layers.pygimplib import pgoperations
from export_layers.pygimplib import pgutils

from export_layers import builtin_operations

from export_layers.pygimplib.tests import stubs_gimp

from .. import config
config.init()

from .. import exportlayers
from .. import operations
from .. import settings_plugin

pygimplib.init()


class TestLayerExporterInitialOperations(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.image = pdb.gimp_image_new(1, 1, gimpenums.RGB)
  
  @classmethod
  def tearDownClass(cls):
    pdb.gimp_image_delete(cls.image)
  
  def test_add_operation_added_operation_is_first_in_execution_list(self):
    settings = settings_plugin.create_settings()
    settings["special/image"].set_value(self.image)
    settings["main/file_extension"].set_value("xcf")
    
    layer_exporter = exportlayers.LayerExporter(
      settings["special/run_mode"].value,
      settings["special/image"].value,
      settings["main"])
    
    operations.add(
      settings["main/operations"],
      builtin_operations.BUILTIN_OPERATIONS["ignore_layer_modes"])
    
    layer_exporter.add_operation(
      pgutils.empty_func, [operations.DEFAULT_OPERATIONS_GROUP])
    
    layer_exporter.export(processing_groups=[])
    
    added_operation_items = layer_exporter.operation_executor.list_operations(
      group=operations.DEFAULT_OPERATIONS_GROUP)
    
    self.assertEqual(len(added_operation_items), 3)
    
    initial_executor = added_operation_items[1]
    self.assertIsInstance(initial_executor, pgoperations.OperationExecutor)
    
    operations_in_initial_executor = initial_executor.list_operations(
      group=operations.DEFAULT_OPERATIONS_GROUP)
    self.assertEqual(len(operations_in_initial_executor), 1)
    self.assertEqual(operations_in_initial_executor[0], (pgutils.empty_func, (), {}))


class TestAddOperationFromSettings(unittest.TestCase):
  
  def setUp(self):
    self.executor = pgoperations.OperationExecutor()
    self.settings = operations.create("operations")
    
    self.procedure_stub = stubs_gimp.PdbProcedureStub(
      name="file-png-save",
      type_=gimpenums.PLUGIN,
      params=(
        (gimpenums.PDB_INT32, "run-mode", "The run mode"),
        (gimpenums.PDB_INT32ARRAY, "save-options", "Save options"),
        (gimpenums.PDB_STRING, "filename", "Filename to save the image in")),
      return_vals=None,
      blurb="Saves files in PNG file format")
  
  def test_add_operation(self):
    operation = operations.add(
      self.settings, builtin_operations.BUILTIN_OPERATIONS["insert_background_layers"])
    
    exportlayers.add_operation_from_settings(operation, self.executor)
    
    added_operation_items = self.executor.list_operations(
      group=operations.DEFAULT_OPERATIONS_GROUP)
    
    self.assertEqual(len(added_operation_items), 1)
    self.assertEqual(added_operation_items[0][1], ("background",))
    self.assertEqual(added_operation_items[0][2], {})
  
  def test_add_pdb_proc_as_operation_without_run_mode(self):
    self.procedure_stub.params = self.procedure_stub.params[1:]
    self._test_add_pdb_proc_as_operation(self.procedure_stub, ((), ""), {})
  
  def test_add_pdb_proc_as_operation_with_run_mode(self):
    self._test_add_pdb_proc_as_operation(self.procedure_stub, ((), ""), {"run_mode": 0})
  
  def _test_add_pdb_proc_as_operation(self, pdb_procedure, expected_args, expected_kwargs):
    operation = operations.add(self.settings, pdb_procedure)
    
    with mock.patch("export_layers.exportlayers.pdb") as pdb_mock:
      pdb_mock.__getitem__.return_value = pdb_procedure
      
      exportlayers.add_operation_from_settings(operation, self.executor)
    
    added_operation_items = self.executor.list_operations(
      group=operations.DEFAULT_OPERATIONS_GROUP)
    
    self.assertEqual(len(added_operation_items), 1)
    self.assertEqual(added_operation_items[0][1], expected_args)
    self.assertDictEqual(added_operation_items[0][2], expected_kwargs)
