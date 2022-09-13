# Copyright (C) 2014-2018 Enzien Audio, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

from .HeavyObject import HeavyObject

class ControlExpr(HeavyObject):
    """Just a stub to get the thing working"""


    c_struct = "ControlExpr"
    preamble = "cExpr"
    _expr = None

    @classmethod
    def get_C_header_set(clazz):
        return {"HvControlExpr.h"}

    @classmethod
    def get_C_file_set(clazz):
        return {"HvControlExpr.h", "HvControlExpr.c"}

    @classmethod
    def get_C_init(clazz, obj_type, obj_id, args):
        clazz._expr = args["expressions"][0]
        eval_f = f"&Heavy_heavy::{clazz.preamble}_{obj_id}_evaluate"
        return [f"cExpr_init(&cExpr_{obj_id}, {eval_f});"]
    """
    """

    @classmethod
    def get_C_def(clazz, obj_type, obj_id):
        lines = ["{0} {1}_{2};".format(
            clazz.get_c_struct(obj_type),
            clazz.get_preamble(obj_type),
            obj_id)]
        lines.append("// --------------- big ol' comment ------------")
        lines.append(f"static float {clazz.preamble}_{obj_id}_evaluate(float* args);")
        return lines
    """
    The get_C_def method creates the object definitions that go into the .hpp file.
    This is a place where other things could be inserted in
    """

    @classmethod
    def get_C_onMessage(clazz, obj_type, obj_id, inlet_index, args):
        return [
            "cExpr_onMessage(_c, &Context(_c)->cExpr_{0}, {1}, m, &cExpr_{0}_sendMessage);".format(
                obj_id,
                inlet_index)
        ]
    """
    The get_C_onMessage method returns the code that will get inserted into
    the cReceive_<UID>_sendMessage method
    """

    # @classmethod
    # def get_C_process(clazz, obj_type, process_dict, objects):
    #     return [
    #         "printf(\"hello world\")"
    #     ]
    """
    The get_C_process method seems to only get called by Signal IR objects, it does
    not get called for Control IR objects
    """

    @classmethod
    def get_C_impl(clazz, obj_type, obj_id, on_message_list, get_obj_class, objects):
        lines = super().get_C_impl(obj_type, obj_id, on_message_list, get_obj_class, objects)
        bound_expr = bind_expr(clazz._expr, "args")
        lines.extend([
            "",
            f"float Heavy_heavy::{clazz.preamble}_{obj_id}_evaluate(float* args) {{",
            f"\treturn {bound_expr};",
            "}",
        ])
        return lines
    """
    Th get_C_impl method overrides the creation of the cExpr_<UID>_sendMessage() method that
    the translator will create as below by default:

    void Heavy_heavy::cExpr_pynQY0UK_sendMessage(HeavyContextInterface *_c, int letIn, const HvMessage *m) {
    cPrint_onMessage(_c, m, "print");
    }
    """


"""
Below is code to rewrite the input expression into one that uses local variables
that have been cast to either float or int
"""

# todo(dgb): need to handle the 's' type
def var_n(a_name, var):
    parts = re.match(r"\$([fi])(\d)", var)
    type = "float" if parts[1] == "f" else "int"
    return f"(({type})({a_name}[{int(parts[2])-1}]))"


def bind_expr(exp="$f1+2", a_name="a"):
    vars = re.findall(r"\$[fis]\d", exp)
    new_exp = exp
    for var in vars:
        new_exp = new_exp.replace(var, var_n(a_name, var))
    return new_exp
