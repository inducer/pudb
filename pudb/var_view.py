# constants and imports -------------------------------------------------------
import urwid

try:
    import numpy
    HAVE_NUMPY = 1
except ImportError:
    HAVE_NUMPY = 0

# data ------------------------------------------------------------------------
class FrameVarInfo(object):
    def __init__(self):
        self.id_path_to_iinfo = {}
        self.watches = []

    def get_inspect_info(self, id_path, read_only):
        if read_only:
            return self.id_path_to_iinfo.get(
                    id_path, InspectInfo())
        else:
            return self.id_path_to_iinfo.setdefault(
                    id_path, InspectInfo())

class InspectInfo(object):
    def __init__(self):
        self.show_detail = False
        self.display_type = "type"
        self.highlighted = False
        self.repeated_at_top = False
        self.show_private_members = False

class WatchExpression(object):
    def __init__(self, expression):
        self.expression = expression

class WatchEvalError(object):
    def __str__(self):
        return "<error>"




# safe types ------------------------------------------------------------------
def get_str_safe_types():
    import types

    return tuple(getattr(types, s) for s in
        "BuiltinFunctionType BuiltinMethodType  ClassType "
        "CodeType FileType FrameType FunctionType GetSetDescriptorType "
        "LambdaType MemberDescriptorType MethodType ModuleType "
        "SliceType TypeType TracebackType UnboundMethodType XRangeType".split()
        if hasattr(types, s)) + (WatchEvalError,)

STR_SAFE_TYPES = get_str_safe_types()




# widget ----------------------------------------------------------------------
class VariableWidget(urwid.FlowWidget):
    def __init__(self, prefix, var_label, value_str, id_path=None, attr_prefix=None,
            watch_expr=None):
        self.prefix = prefix
        self.var_label = var_label
        self.value_str = value_str
        self.id_path = id_path
        self.attr_prefix = attr_prefix or "var"
        self.watch_expr = watch_expr

    def selectable(self):
        return True

    SIZE_LIMIT = 20

    def rows(self, size, focus=False):
        if (self.value_str is not None
                and self.var_label is not None
                and len(self.prefix) + len(self.var_label) > self.SIZE_LIMIT):
            return 2
        else:
            return 1

    def render(self, size, focus=False):
        maxcol = size[0]
        if focus:
            apfx = "focused "+self.attr_prefix+" "
        else:
            apfx = self.attr_prefix+" "

        if self.value_str is not None:
            if self.var_label is not None:
                if len(self.prefix) + len(self.var_label) > self.SIZE_LIMIT:
                    # label too long? generate separate value line
                    text = [self.prefix + self.var_label,
                            self.prefix+"  " + self.value_str]

                    attr = [[(apfx+"label", len(self.prefix)+len(self.var_label))],
                            [(apfx+"value", len(self.prefix)+2+len(self.value_str))]]
                else:
                    text = [self.prefix + self.var_label +": " + self.value_str]

                    attr = [[
                            (apfx+"label", len(self.prefix)+len(self.var_label)+2),
                            (apfx+"value", len(self.value_str)),
                            ]]
            else:
                text = [self.prefix + self.value_str]

                attr = [[
                        (apfx+"label", len(self.prefix)),
                        (apfx+"value", len(self.value_str)),
                        ]]
        else:
            text = [self.prefix + self.var_label]

            attr = [[ (apfx+"label", len(self.prefix) + len(self.var_label)), ]]

        from pudb.ui_tools import make_canvas
        return make_canvas(text, attr, maxcol, apfx+"value")

    def keypress(self, size, key):
        return key




# tree walking ----------------------------------------------------------------
class ValueWalker:
    def __init__(self, frame_var_info):
        self.frame_var_info = frame_var_info

    def walk_value(self, prefix, label, value, id_path=None, attr_prefix=None):
        if id_path is None:
            id_path = label

        iinfo = self.frame_var_info.get_inspect_info(id_path, read_only=True)

        if isinstance(value, (int, float, long, complex)):
            self.add_item(prefix, label, repr(value), id_path, attr_prefix)
        elif isinstance(value, (str, unicode)):
            self.add_item(prefix, label, repr(value)[:200], id_path, attr_prefix)
        else:
            if iinfo.display_type == "type":
                if HAVE_NUMPY and isinstance(value, numpy.ndarray):
                    displayed_value = "ndarray %s %s" % (value.dtype, value.shape)
                elif isinstance(value, STR_SAFE_TYPES):
                    displayed_value = str(value)
                else:
                    displayed_value = type(value).__name__
            elif iinfo.display_type == "repr":
                displayed_value = repr(value)
            elif iinfo.display_type == "str":
                displayed_value = str(value)
            else:
                displayed_value = "ERROR: Invalid display_type"

            self.add_item(prefix, label,
                displayed_value, id_path, attr_prefix)

            if not iinfo.show_detail:
                return

            # set ---------------------------------------------------------
            if isinstance(value, (set, frozenset)):
                for i, entry in enumerate(value):
                    if i % 10 == 0 and i:
                        cont_id_path = "%s.cont-%d" % (id_path, i)
                        if not self.frame_var_info.get_inspect_info(
                                cont_id_path, read_only=True).show_detail:
                            self.add_item(prefix+"  ", "...", None, cont_id_path)
                            break

                    self.walk_value(prefix+"  ", None, entry,
                        "%s[%d]" % (id_path, i))
                if not value:
                    self.add_item(prefix+"  ", "<empty>", None)
                return

            # containers --------------------------------------------------
            key_it = None
            try:
                l = len(value)
            except:
                pass
            else:
                try:
                    value[0]
                except IndexError:
                    key_it = []
                except:
                    pass
                else:
                    key_it = xrange(l)

            try:
                key_it = value.iterkeys()
            except:
                pass

            if key_it is not None:
                cnt = 0
                for key in key_it:
                    if cnt % 10 == 0 and cnt:
                        cont_id_path = "%s.cont-%d" % (id_path, cnt)
                        if not self.frame_var_info.get_inspect_info(
                                cont_id_path, read_only=True).show_detail:
                            self.add_item(
                                prefix+"  ", "...", None, cont_id_path)
                            break

                    self.walk_value(prefix+"  ", repr(key), value[key],
                        "%s[%r]" % (id_path, key))
                    cnt += 1
                if not cnt:
                    self.add_item(prefix+"  ", "<empty>", None)
                return

            # class types -------------------------------------------------
            key_its = []
            try:
                key_its.append(value.__slots__)
            except:
                pass

            try:
                key_its.append(value.__dict__.iterkeys())
            except:
                pass

            if not key_its:
                try:
                    key_its.append(dir(value))
                except:
                    pass

            keys = [key for key_it in key_its for key in key_it]
            keys.sort()

            cnt_omitted = 0

            for key in keys:
                if key[0] == "_" and not iinfo.show_private_members:
                    cnt_omitted += 1
                    continue

                try:
                    attr_value = getattr(value, key)
                except:
                    attr_value = WatchEvalError()

                self.walk_value(prefix+"  ",
                        ".%s" % key, attr_value,
                        "%s.%s" % (id_path, key))

            if not keys:
                if cnt_omitted:
                    self.add_item(prefix+"  ", "<omitted private attributes>", None)
                else:
                    self.add_item(prefix+"  ", "<empty>", None)

            if not key_its:
                self.add_item(prefix+"  ", "<?>", None)




class BasicValueWalker(ValueWalker):
    def __init__(self, frame_var_info):
        ValueWalker.__init__(self, frame_var_info)

        self.widget_list = []

    def add_item(self, prefix, var_label, value_str, id_path=None, attr_prefix=None):
        iinfo = self.frame_var_info.get_inspect_info(id_path, read_only=True)
        if iinfo.highlighted:
            attr_prefix = "highlighted var"

        self.widget_list.append(
                VariableWidget(prefix, var_label, value_str, id_path, attr_prefix))




class WatchValueWalker(ValueWalker):
    def __init__(self, frame_var_info, widget_list, watch_expr):
        ValueWalker.__init__(self, frame_var_info)
        self.widget_list = widget_list
        self.watch_expr = watch_expr

    def add_item(self, prefix, var_label, value_str, id_path=None, attr_prefix=None):
        iinfo = self.frame_var_info.get_inspect_info(id_path, read_only=True)
        if iinfo.highlighted:
            attr_prefix = "highlighted var"

        self.widget_list.append(
                VariableWidget(prefix, var_label, value_str, id_path, attr_prefix,
                    watch_expr=self.watch_expr))




class TopAndMainVariableWalker(ValueWalker):
    def __init__(self, frame_var_info):
        ValueWalker.__init__(self, frame_var_info)

        self.main_widget_list = []
        self.top_widget_list = []

        self.top_id_path_prefixes = []

    def add_item(self, prefix, var_label, value_str, id_path=None, attr_prefix=None):
        iinfo = self.frame_var_info.get_inspect_info(id_path, read_only=True)
        if iinfo.highlighted:
            attr_prefix = "highlighted var"

        repeated_at_top = iinfo.repeated_at_top
        if repeated_at_top and id_path is not None:
            self.top_id_path_prefixes.append(id_path)

        for tipp in self.top_id_path_prefixes:
            if id_path is not None and id_path.startswith(tipp):
                repeated_at_top = True

        if repeated_at_top:
            self.top_widget_list.append(
                    VariableWidget(prefix, var_label, value_str, id_path, attr_prefix))

        self.main_widget_list.append(
                VariableWidget(prefix, var_label, value_str, id_path, attr_prefix))




# top level -------------------------------------------------------------------
SEPARATOR = urwid.AttrWrap(urwid.Text(""), "variable separator")

def make_var_view(frame_var_info, locals, globals):
    vars = locals.keys()
    vars.sort(key=lambda n: n.lower())

    tmv_walker = TopAndMainVariableWalker(frame_var_info)
    ret_walker = BasicValueWalker(frame_var_info)
    watch_widget_list = []

    for watch_expr in frame_var_info.watches:
        try:
            value = eval(watch_expr.expression, globals, locals)
        except:
            value = WatchEvalError()

        WatchValueWalker(frame_var_info, watch_widget_list, watch_expr) \
                .walk_value("", watch_expr.expression, value)

    if "__return__" in vars:
        ret_walker.walk_value("", "Return", locals["__return__"], attr_prefix="return")

    for var in vars:
        if not var[0] in "_.":
            tmv_walker.walk_value("", var, locals[var])

    result = tmv_walker.main_widget_list

    if watch_widget_list:
        result = (watch_widget_list + [SEPARATOR] + result)

    if tmv_walker.top_widget_list:
        result = (tmv_walker.top_widget_list + [SEPARATOR] + result)

    if ret_walker.widget_list:
        result = (ret_walker.widget_list + result)

    return result




class FrameVarInfoKeeper(object):
    def __init__(self):
        self.frame_var_info = {}

    def get_frame_var_info(self, read_only, ssid=None):
        if ssid is None:
            ssid = self.debugger.get_stack_situation_id()
        if read_only:
            return self.frame_var_info.get(ssid, FrameVarInfo())
        else:
            return self.frame_var_info.setdefault(ssid, FrameVarInfo())

