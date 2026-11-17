def devalue(arr):
    memo = {}
    def r(i):
        if not isinstance(i, int) or i < 0: return None
        if i in memo: return memo[i]
        v = arr[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"): out = r(v[1])
            elif v and isinstance(v[0], str) and v[0] in ("Set", "Map", "Date"): out = v[1:]
            else:
                out = []; memo[i] = out; out.extend(r(x) for x in v); return out
        elif isinstance(v, dict):
            out = {}; memo[i] = out
            for k, x in v.items(): out[k] = r(x)
            return out
        else: out = v
        memo[i] = out; return out
    return r(0)
