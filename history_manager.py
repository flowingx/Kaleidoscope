# history_manager.py
"""
实现了命令模式，用于管理所有可撤销/重做的操作。
包含一个 Action 基类和多个具体的动作子类，以及 HistoryManager 本身。
"""

class Action:
    """所有可撤销动作的基类。"""
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError

class AddLayerAction(Action):
    """记录“添加新图层”的动作。"""
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

class AddShapeAction(Action):
    """记录“添加新矢量形状”的动作。"""
    def __init__(self, layer, shape):
        self.layer = layer
        self.shape = shape
    def execute(self): self.layer.shapes.append(self.shape)
    def undo(self): self.layer.shapes.remove(self.shape)

class DeleteShapeAction(Action):
    """记录“删除矢量形状”的动作。"""
    def __init__(self, layer, shape):
        self.layer = layer
        self.shape = shape
    def execute(self): self.layer.shapes.remove(self.shape)
    def undo(self): self.layer.shapes.append(self.shape)

class ModifyShapeAction(Action):
    """记录对矢量形状属性（如位置、大小、旋转）的修改。"""
    def __init__(self, shape, old_attrs, new_attrs):
        self.shape = shape
        self.old_attrs = old_attrs
        self.new_attrs = new_attrs
    def execute(self):
        for attr, value in self.new_attrs.items(): setattr(self.shape, attr, value)
    def undo(self):
        for attr, value in self.old_attrs.items(): setattr(self.shape, attr, value)

class HistoryManager:
    """
    管理一个撤销栈和一个重做栈，以处理所有 Action 对象。
    """
    def __init__(self, app):
        self.app = app
        self.undo_stack = []
        self.redo_stack = []

    def execute_action(self, action: Action):
        """执行一个新动作，并将其推入撤销栈。"""
        action.execute()
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self):
        """从撤销栈中弹出一个动作，执行其 undo 方法，并将其推入重做栈。"""
        if self.can_undo():
            action = self.undo_stack.pop()
            action.undo()
            self.redo_stack.append(action)

    def redo(self):
        """从重做栈中弹出一个动作，执行其 execute 方法，并将其推入撤销栈。"""
        if self.can_redo():
            action = self.redo_stack.pop()
            action.execute()
            self.undo_stack.append(action)

    def can_undo(self):
        """检查撤销栈是否为空。"""
        return bool(self.undo_stack)

    def can_redo(self):
        """检查重做栈是否为空。"""
        return bool(self.redo_stack)

# Keep existing layer actions for backward compatibility
class DeleteLayerAction(Action):
    """记录“删除图层”的动作。"""
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
    """记录“清空所有图层”的动作。"""
    def __init__(self, app, cleared_layers):
        self.app = app
        self.cleared_layers = cleared_layers
    def execute(self):
        self.app.layers = [self.app.layers[-1]]
        self.app.active_layer_index = 0
        self.app._update_layer_list_ui()
    def undo(self):
        self.app.layers = self.cleared_layers + self.app.layers
        self.app.active_layer_index = 0
        self.app._update_layer_list_ui()

class AddPixelAction(Action):
    """记录一次完整的像素笔刷绘制动作（线、圆、喷涂）。"""
    def __init__(self, layer, path, brush_type, draw_func):
        self.layer = layer
        self.path = path
        self.brush_type = brush_type
        self.draw_func = draw_func
        self.undo_surface = None

    def execute(self):
        """执行绘制，并在绘制前保存图层快照。"""
        self.undo_surface = self.layer.surface.copy()
        self.draw_func(self.layer.surface, self.path, self.brush_type)

    def undo(self):
        """通过恢复快照来撤销绘制。"""
        if self.undo_surface:
            self.layer.surface.blit(self.undo_surface, (0, 0))