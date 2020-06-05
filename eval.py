from ann import read_ann


def overlapping(predicted, reference):
    n = 0  # index for reference entities
    matches = []
    insertions = []  # false positives (in predicted)
    deletions = []  # false negatives (in reference)
    for m, p in enumerate(predicted):
        ms = []
        end = False
        while not end and n < len(reference):
            r = reference[n]
            if before(r, p):
                deletions.append(n)
                n += 1
            elif overlaps(r, p):
                ms.append(n)
                if r[-1] < p[-1]:
                    # r ends before p: jr < jp
                    # advance to next r
                    n += 1
                else:
                    # r ends after p: jr >= jp
                    # r may overlap also with next p
                    end = True
            else:
                assert after(r, p)
                end = True

        matches.append(ms)
        if ms == []:
            insertions.append(m)

    return matches, insertions, deletions


def before(r, p):
    ir, jr = r[-2:]
    ip, jp = p[-2:]
    return jr <= ip


def overlaps(r, p):
    ir, jr = r[-2:]
    ip, jp = p[-2:]
    return ip < jr and ir < jp


def after(r, p):
    ir, jr = r[-2:]
    ip, jp = p[-2:]
    return jp <= ir


def jaccard(r, p):
    ir, jr = r[-2:]
    ip, jp = p[-2:]

    ov = min(jr, jp) - max(ir, ip)
    lr = jr - ir
    lp = jp - ip
    return float(ov) / float(lr + lp - ov)


def match(predicted, reference):
    overlappings, insertions, deletions = overlapping(predicted, reference)

    matches = []
    scores = []
    matched = set()
    for p, ovs in zip(predicted, overlappings):
        max_sim = 0.0
        max_i = -1
        for i in set(ovs) - matched:
            r = reference[i]
            sim = jaccard(r, p)
            if sim > max_sim:
                # XXX: what if there are ties?
                max_sim = sim
                max_i = i

        matches.append(max_i)
        scores.append(max_sim)
        matched.add(max_i)

    return matches, scores


def eval(reference, predicted):
    matches, scores = match(predicted, reference)
    m = sum(scores)
    if len(predicted) > 0.0:
        precision = m / len(predicted)
    else:
        precision = 0.0
    if len(reference) > 0.0:
        recall = m / len(reference)
    else:
        recall = 0.0
    print(f'Precision: {precision} ({m} / {len(predicted)})')
    print(f'Recall: {recall} ({m} / {len(reference)})')


if __name__ == '__main__':
    import sys
    argv = sys.argv
    if len(argv) < 4:
        print('Usage: python eval.py <source.txt> <reference.ann> <predicted.ann> [<entity_type>]')
    else:
        if len(argv) == 5:
            etypes = [argv[4]]
        else:
            etypes = [
                'Anatomical_Entity',
                'Location',
                'Finding',
                'Negation'
            ]
        ref = read_ann(argv[2])
        pred = read_ann(argv[3])
        for etype in etypes:
            print('Entity:', etype)
            eref = [r for r in ref if r[0] == etype]
            epred = [p for p in pred if p[0] == etype]
            eval(eref, epred)
            print('')
