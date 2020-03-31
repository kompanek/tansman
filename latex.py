import ast
import itertools

LATEX_TEMPLATE = '''


'''


class LatexBuilder:
    def __init__(self, code):
        self.code = code
        self.tree = ast.parse(code)

    def build_string(self):
        self.tree = ast.parse(self.code)
        result = self._build(self.tree)
        r1 = self._tree_to_string(result)
        r2 = self._cleanup_string(r1)
        return r2

    def _normalize_name(self, name):
        name = name.replace("delta", "\\delta")

        if "_" in name: # Treat it like it has a subscript
            parts = name.split("_")
            name = parts[0] + "_" + "{" + parts[1] + "}"
        return "\\mathit{" + name + "}"

    def _cleanup_string(self, result):
        for t, val in enumerate(result):
            if t > (len(result) - 4):
                break
            if result[t] == "\\ \\forall":
                if result[t+3] == "\\ \\forall":
                    result[t+2] = ""
        return result


    def _tree_to_string(self, results):
        flattened = []
        if type(results) is list:
            for c in results:
                flattened.append(self._tree_to_string(c))
        else:
            return [results]
        results = list(itertools.chain(*flattened))
        return results

    def _recurse(self, children, results):
        # Recurse over children
        for child in children:
            child_result = self._build(child)
            if len(child_result) > 1:
                results.append(child_result)
            elif len(child_result) == 1:
                results.append(child_result[0])
        return results

    def _build(self, node):
        results = []
        if type(node) is ast.For:
            self._recurse(node.body, results)
            results = results + ["\\ \\forall", node.target.id, "\\\\ \n"]
        elif type(node) is ast.AugAssign:
            results = []
            self._recurse([node.value], results)
        elif type(node) is ast.BinOp:
            self._recurse(ast.iter_child_nodes(node), results)
        elif type(node) is ast.Compare:
            if type(node.ops[0]) is ast.LtE:
                results = ["\\leq"]
            elif type(node.ops[0]) is ast.GtE:
                results = ["\\geq"]
            elif type(node.ops[0]) is ast.Eq:
                results = ["="]
            else:
                results = []
            operands = []
            self._recurse([node.left] + node.comparators, operands)
            results = [operands[0]] + results
            if len(operands) > 1:
                results = results + [operands[1]]
        elif type(node) is ast.comprehension:
            results = [self._normalize_name(node.target.id)]
            results = self._recurse([node.iter], results)
        elif type(node) is ast.Call:
            if node.func.id == "sum":
                self._recurse(node.args, results)
                results = ["\\sum_{", results[0][1],  "}", "{", results[0][0], "}"]
            elif node.func.id == "range":
                index = "UNK"
                self._recurse(node.args, results)
                start = results[0]; end = results[1]
                results = ["\\in {} \\ldots {}".format(start, end)]
        elif type(node) is ast.Num:
            results = [node.n]
        elif type(node) is ast.Attribute:
            results = ["{" + self._normalize_name(node.attr) + "}"]
        # elif type(node) is ast.Name: # This is redundant and breaks things. FIXME: understand why
        #    results = ["{" + self._normalize_name(node.id) + "}"]
        elif type(node) is ast.Index:  # <node.e.id1, .. node.e.idN>
            if type(node.value) is ast.Tuple:
                index_names = [self._normalize_name(e.id) for e in node.value.elts]
                return index_names
            elif type(node.value) is ast.Name:  # <node.value>.id
                return ["{" + self._normalize_name(node.value.id) + "}"]
            else:
                return [str(node.value)]
        elif type(node) is ast.Subscript:  # <node.value>[<node.slice>]
            self._recurse([node.value, node.slice], results)
            value = results[0]
            if type(results[1]) is list:
                slice_value = ",".join(results[1])
            else:
                slice_value = results[1]
            results = ["{}_{{{}}}".format(value, slice_value)]
        else:
            self._recurse(ast.iter_child_nodes(node), results)
        return results


SNIPPET = '''
for i in range(0, self.N_ITEMS):
    self += sum(self.P[(i, t)] for t in range(0, self.N_SLOTS)) >= self.TIMEPERITEM[i]    
for t in range(0, self.n_slots):
    self += sum(self.practice[(i, t)] for i in range(0, self.n_items)) <= self.time_available[t]
for i in range(0, self.n_items):
    self += sum(self.practice[(i, t)] for t in range(0, self.n_slots)) >= self.time_per_item[i]
for i in range(0, self.n_items):
    for t in range(0, self.n_slots):
        self += (self.time_so_far[(i, t)] == sum(self.practice[(i, t0)] for t0 in range(0, t-1)))
for i in range(0, self.n_items):
    for t in range(0, self.n_slots):
        self += self.practice[(i, t)] <= 2
'''

SNIPPET2 = '''
self.objective = COEFFTIMELINESS*item_timeliness_metric + COEFFFUNTOTAL*fun_total - COEFFTOTALPRACTICETIME*totalpracticetime
for t in range(0, self.n_slots):
    self += sum(self.practice[(i, t)] for i in range(0, self.n_items)) <= self.timeavailable[t]
for i in range(0, self.n_items):
    self += sum(self.practice[(i, t)] for t in range(0, self.n_slots)) >= self.timeperitem[i]
for i in range(0, self.n_items):
    for t in range(0, self.n_slots):
        self += (self.timesofar[(i, t)] == sum(self.practice[(i, t0)] for t0 in range(0, t-1)))
for i in range(0, self.n_items):
    for t in range(0, self.n_slots):
        self += self.practice[(i, t)] <= 2
for i in range(0, self.n_items):
    for t in range(0, self.n_slots - self.windowsize - 1):
        self += sum(self.practice[(i, t_delta)] for t_delta in range(0, self.windowsize)) >= self.minpracticeperwindow
for i in range(0, self.n_items):
    for t in range(0, self.n_slots - self.windowsize - 1):
        self += sum(self.practice[(i, t_delta)] for t_delta in range(0, self.windowsize)) <= self.maxpracticeperwindow
'''


def main():
    v = LatexBuilder(SNIPPET2)
    r = v.build_string()
    print(" ".join(str(v) for v in r))


if __name__ == "__main__":
    main()
