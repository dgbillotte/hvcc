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

from .expr_c_writer import ExprCWriter
from .HeavyObject import HeavyObject


class SignalExpr(HeavyObject):
    """Handles the math objects.
    """

    preamble = "cExprSig"

    obj_eval_functions = {}

    @classmethod
    def handles_type(clazz, obj_type):
        """Returns true if the object type can be handled by this class
        """
        return obj_type == "_expr~"

    @classmethod
    def get_C_header_set(clazz):
        return {"HvMath.h"}

    @classmethod
    def get_C_class_header_code(clazz, obj_type, args):
        eval_funcs = ", ".join(clazz.obj_eval_functions.values())
        fptr_type = f"{clazz.preamble}_evaluator"
        lines = [
            f"typedef void(*{fptr_type})(hv_bInf_t*, hv_bOutf_t);",
            f"{fptr_type} {clazz.preamble}_evaluators[{len(clazz.obj_eval_functions)}] = {{{eval_funcs}}};",
        ]
        return lines

    @classmethod
    def get_C_obj_header_code(clazz, obj_type, obj_id, args):
        lines = super().get_C_obj_header_code(obj_type, obj_id, args)
        func_name = f"{clazz.preamble}_{obj_id}_evaluate"
        clazz.obj_eval_functions[obj_id] = func_name
        lines.extend([
            f"static inline void {func_name}(hv_bInf_t* bIns, hv_bOutf_t bOut);",
        ])
        return lines

    @classmethod
    def get_C_obj_impl_code(clazz, obj_type, obj_id, args):
        """
        (Per object) this creates the _sendMessage function that other objects use to
        send messages to this object.
        """

        lines = super().get_C_obj_impl_code(obj_type, obj_id, args)

        expr = args["expressions"][0]
        expr_parser = ExprCWriter(expr)
        expr_lines = expr_parser.to_c_simd("bIns", "bOut")[:-1]
        expr_lines = "\n".join(
            [f"\t{line}" for line in expr_lines]
        )
        num_buffers = expr_parser.num_simd_buffers()
        buffer_declaration = "\t// no extra buffers needed"
        if num_buffers > 0:
            buffers = ", ".join([f"Bf{i}" for i in range(0, num_buffers)])
            buffer_declaration = f"\thv_bufferf_t {buffers};"

        func_name = f"Heavy_heavy::{clazz.preamble}_{obj_id}_evaluate"
        lines.extend([
            "",
            f"void {func_name}(hv_bInf_t* bIns, hv_bOutf_t bOut) {{",

            buffer_declaration,
            expr_lines,
            "}",

        ])
        return lines

    @classmethod
    def get_C_process(clazz, process_dict, obj_type, obj_id, args):
        input_args = []
        for b in process_dict["inputBuffers"]:
            buf = HeavyObject._c_buffer(b)
            input_args.append(f"VIf({buf})")
        out_buf = HeavyObject._c_buffer(process_dict["outputBuffers"][0])
        out_buf = f"VOf({out_buf})"

        call = [
            "",
            "\t// !!! declare this buffer once outside the loop",
            f"\thv_bInf_t input_args_{obj_id}[{args['num_inlets']}] = {{{', '.join(input_args)}}};",
            f"\t{clazz.preamble}_evaluators[{len(clazz.obj_eval_functions)}](input_args_{obj_id}, {out_buf});"
            "",
        ]

        return call
