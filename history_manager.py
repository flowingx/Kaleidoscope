# history_manager.py

class Action:
    """Base class for all actions that can be undone."""
    def execute(self):
        raise NotImplementedError
    def undo(self):
        raise NotImplementedError

class AddLayerAction(Action):
    def __init__(self, app, layer):
        self.app = app
        self.layer = layer

    def execute(self):
        self.app.layers.insert(0, self.layer)
        self.app.active_layer_index = 0
        self.app._update_layer_list_ui()

    def undo(self):
        self.app.layers.remove(self.layer)
        self.app.active_layer_index = min(self.app.active_layer_index, len(self.app.layers) - 1)
        self.app._update_layer_list_ui()

class DeleteLayerAction(Action):
    def __init__(self, app, layer, index):
        self.app = app
        self.layer = layer
        self.index = index

    def execute(self):
        self.app.layers.pop(self.index)
        self.app.active_layer_index = min(self.index, len(self.app.layers) - 1)
        self.app._update_layer_list_ui()
    
    def undo(self):
        self.app.layers.insert(self.index, self.layer)
        self.app.active_layer_index = self.index
        self.app._update_layer_list_ui()

class ClearAllAction(Action):
    def __init__(self, app, cleared_layers):
        self.app = app
        self.cleared_layers = cleared_layers

    def execute(self):
        self.app.layers = [self.app.layers[-1]] # Keep only background
        self.app.active_layer_index = 0
        self.app._update_layer_list_ui()

    def undo(self):
        self.app.layers = self.cleared_layers + self.app.layers
        self.app.active_layer_index = 0
        self.app._update_layer_list_ui()

class HistoryManager:
    def __init__(self, app):
        self.app = app
        self.undo_stack = []
        self.redo_stack = []

    def execute_action(self, action: Action):
        action.execute()
        self.undo_stack.append(action)
        self.redo_stack.clear() # A new action invalidates the redo history

    def undo(self):
        if self.can_undo():
            action = self.undo_stack.pop()
            action.undo()
            self.redo_stack.append(action)

    def redo(self):
        if self.can_redo():
            action = self.redo_stack.pop()
            action.execute()
            self.undo_stack.append(action)

    def can_undo(self):
        return bool(self.undo_stack)

    def can_redo(self):
        return bool(self.redo_stack)