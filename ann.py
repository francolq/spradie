

def read_ann(ann):
    with open(ann) as f:
        entities = []
        for line in f:
            if line[0] == 'T':
                sline = line.split()
                if ';' in sline[3]:
                    print('Skipped non-contiguous entity:', ' '.join(sline))
                else:
                    e = (sline[1], int(sline[2]), int(sline[3]))
                    entities.append(e)
        
        sorted_entities = sorted(entities, key=lambda e: e[1])
        return sorted_entities
