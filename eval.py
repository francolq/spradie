from ann import read_ann


def overlapping(predicted, reference):
    """Compute overlappings between predicted and reference sets.
    Entities in the same set may overlap (it's a bit messy).

    Input:
    predicted -- list of pairs (i, j), sorted by i and then by j
    reference -- list of pairs (i, j), sorted by i and then by j

    Output: 3-uple (matches, insertions, deletions) where
    matches -- for each predicted entity, list of overlapping reference entities
    (list of list of indexes)
    insertions -- predicted entities not overlapping with any reference entity
    (list of indexes)
    deletions -- reference entities not overlapping with any prediction
    (list of indexes)
    """
    n = 0  # index for reference entities
    matches = []
    insertions = []  # false positives (in predicted)
    deletions = []  # false negatives (in reference)
    for m, p in enumerate(predicted):
        ms = []
        end = False
        n2 = n
        while not end and n2 < len(reference):
            r = reference[n2]
            if before(r, p):
                deletions.append(n2)
                n2 += 1  # n will advance also
                n += 1
            elif overlaps(r, p):
                ms.append(n2)
                n2 += 1
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


def jaccard(rs, ps):
    if isinstance(rs, tuple):
        rs = [rs]
    if isinstance(ps, tuple):
        ps = [ps]
    lr = sum(j - i for i, j in rs)
    lp = sum(j - i for i, j in ps)
    
    # XXX: there is for sure a more efficient version
    ov = 0
    for ir, jr in rs:
        for ip, jp in ps:
            ov += max(min(jr, jp) - max(ir, ip), 0)

    return float(ov) / float(lr + lp - ov)


def match(predicted, reference, overlappings):
    """
    Input:
    predicted -- list of predicted entities as returned by read_ann
    reference -- list of reference entities as returned by read_ann
    overlappings -- list of overlappings as returned by overlapping

    Output: a pair (matches, scores) where
    matches -- for each predicted entity, the best matching reference entity (an index)
    scores -- for each predicted entity, the score for the best matching reference entity (a Jaccard Index)
    """
    matches = []
    scores = []
    matched = set()
    for p, ovs in zip(predicted, overlappings):
        max_sim = 0.0
        max_i = -1
        for i in set(ovs) - matched:
            r = reference[i]
            sim = jaccard(r[1], p[1])
            if sim > max_sim:
                # if there are ties, keep the first one
                max_sim = sim
                max_i = i

        matches.append(max_i)
        scores.append(max_sim)
        matched.add(max_i)
    
    return matches, scores


def eval(reference, predicted):
    # convert entities to the format expected by the overlapping function
    pred2 = [(e[1][0][0], e[1][-1][1]) for e in predicted]
    ref2 = [(e[1][0][0], e[1][-1][1]) for e in reference]
    overlappings, insertions, deletions = overlapping(pred2, ref2)

    # Lentient Precision, Recall and F1
    matches, scores = match(predicted, reference, overlappings)
    m = sum(scores)
    if len(predicted) > 0:
        precision = m / len(predicted)
    else:
        precision = 0.0
    if len(reference) > 0:
        recall = m / len(reference)
    else:
        recall = 0.0
    if precision > 0.0 and recall > 0.0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    print(f'Precision: {precision} ({m} / {len(predicted)})')
    print(f'Recall: {recall} ({m} / {len(reference)})')
    print(f'F1: {f1}')

    # Slot Error Rate (SER)
    substitutions = [s for s in scores if s > 0.0 and s < 1.0]
    subs = len(substitutions)
    ins = len(insertions)
    dels = len(deletions)
    ser_num = subs + ins + dels
    if len(reference) > 0:
        ser = float(ser_num) / len(reference)
    else:
        ser = float('nan')
    print(f'Substitutions: {subs}')
    print(f'Insertions: {ins}')
    print(f'Deletions: {dels}')
    print(f'SER: {ser} ({ser_num} / {len(reference)})')


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
