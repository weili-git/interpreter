from Semantic import *


class Interpreter(NodeVisitor):
    def __init__(self):
        self.call_stack = CallStack()

    def visit_BinOp(self, node):
        if node.op.value == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.value == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.value == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.value == '/':
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.value == '//':
            return self.visit(node.left) // self.visit(node.right)
        # elif node.op.value == '**':
        #     return self.visit(node.left) ** self.visit(node.right)

    def visit_UnaryOp(self, node):
        op = node.op.value
        if op == '+':
            return +self.visit(node.expr)
        if op == '-':
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def visit_Bool(self, node):
        return node.value

    def visit_String(self, node):
        return node.value

    def visit_Program(self, node):

        ar = ActivationRecord(
            name="mylang",
            type=ARType.PROGRAM,
            nesting_level=1,
        )
        self.call_stack.push(ar)
        self.visit(node.block)
        self.call_stack.pop()

    def visit_NoOp(self, node):     # dummy node
        return "No operation."

    def visit_Assign(self, node):
        var_name = node.left.value
        var_value = self.visit(node.right)
        ar = self.call_stack.peek()
        ar[var_name] = var_value
        return "Assign {} with {}".format(var_name, var_value)

    def visit_Var(self, node):
        var_name = node.value

        ar = self.call_stack.peek()
        var_value = ar[var_name]
        if var_value is None:
            raise Exception("Undefined identifier: " + var_name)
        else:
            return var_value

    def visit_FunCall(self, node):
        proc_name = node.proc_name

        ar = ActivationRecord(
            name=proc_name,
            type=ARType.PROCEDURE,
            nesting_level=2
        )
        proc_symbol = node.proc_symbol

        formal_params = proc_symbol.formal_params
        actual_params = node.actual_params
        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)
        self.call_stack.push(ar)
        self.visit(proc_symbol.block_ast)
        self.call_stack.pop()
        return "Call {}, params {}".format(node.name, node.params)

    def visit_Defun(self, node):
        return "defun {}, params {}, block {}".format(node.name.value, node.params, node.block)

    def visit_CondPair(self, node):
        if self.visit(node.cond) not in [0, False, None]:
            return node.block
        else:
            return None

    def visit_Condition(self, node):
        for pair in node.pair_list:
            res = self.visit(pair)
            if res:
                return res
        return node.else_block

    def visit_Block(self, node):
        pass

    def interpret(self, tree):
        return self.visit(tree)


def main():
    with open("test02.txt") as f:
        text = f.read()
        tree = Parser(text).parse()

        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.visit(tree)

        interpreter = Interpreter()
        interpreter.interpret(tree)


if __name__ == '__main__':
    main()

# https://github.com/rspivak/lsbasi/blob/master/part19/spi.py