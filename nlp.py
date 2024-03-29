import nltk
from nltk.corpus import brown, verbnet, wordnet
from nltk.chunk.regexp import *
import colorama
from nltk.stem import PorterStemmer,LancasterStemmer
from nltk.stem import WordNetLemmatizer




import json
def syns_load():
    f = open("syns.txt", "r",newline='\n')
    lines = f.readlines()
    syns = []
    for line in lines:
        nl =line.rstrip('\n').split(',')
        syns.append(nl)
    f.close()
    return syns


"""checks if the provided command entities are listed as a synonym of the root words 
    used in extension commands title"""
def alternatives(syns,entities):
    lemmatizer = WordNetLemmatizer()
    for word in entities:
        tokens = nltk.word_tokenize(word)
        token_syns = []
    
    for token in tokens:
        root_found = False #root word for a token found
        roots= []
        for syn_row in syns:
            for registerd_synonym in syn_row:
                if lemmatizer.lemmatize(registerd_synonym)==lemmatizer.lemmatize(token):
                    root_found = True
                    roots.append(lemmatizer.lemmatize(syn_row[0]))
        if root_found == False:
            roots.append('')
        token_syns.append((token,roots))
    return token_syns #return the token and their roor words

def entity_action_recognizer(sentence,prefixed):
    #python_specific_entities = ['for loop','while loop','for number loop','nested for loop','if else ladder','if ladder','nested for number loop','try ladder']

    sentence = sentence.lower()
    tokens = nltk.word_tokenize(sentence)
    default_pos_tags = nltk.pos_tag(tokens)
    lemmatizer = WordNetLemmatizer()

    grammar_np = r"""
                    Entity: {<VBG><NN>}
                    Entity: {<VBG><NNS>}
                    Entity: {<VBN><NN>}
                    Entity: {<VBN><NNS>}
                    Entity: {<VBD><NN>}
                    Entity: {<VBG><NNS>}
                    Entity: {<JJ><NN+>}
                    Entity: {<NN><NN|NNS>*}
                    Entity: {<NNS>}
                    Entity: {<NN>}
                    
                    
                    MultiEntity: {<Entity><IN><Entity>}
                    MultiEntity: {<Entity><IN><DT><Entity>}
                    Action: {<VB>}              
                """
    chunk_parser = nltk.RegexpParser(grammar_np)
    chunk_result = chunk_parser.parse(default_pos_tags)
    entities = []
    for subtree in chunk_result.subtrees(filter=lambda t: t.label() == 'Entity'):
        entity = []
        for item in subtree:
            entity.append(lemmatizer.lemmatize(item[0]))
        entities.append(' '.join(entity))
    actions = []
    for subtree in chunk_result.subtrees(filter=lambda t: t.label() == 'Action'):
        for item in subtree:
            actions.append(item[0])
    preposition = ''
    for subtree in chunk_result.subtrees(filter=lambda t: t.label() == 'MultiEntity'):
        if len(subtree)!=0:
            preposition = subtree[1][0]
    return entities,actions, preposition

def identify_command2(entities,actions,preposition):
    # print(colorama.Fore.CYAN+'*** Searching for command to run.')
    # print(colorama.Fore.BLUE +'Entities received [cmd_entities]: ',entities)
    # print(colorama.Fore.BLUE +'Actions received [cmd_actions]: ',actions)
    
    stemmer = PorterStemmer()
    packageFile = open('package.json')
    package = json.load(packageFile)
    syns = syns_load()
    entity_match = set()
    action_match = set()
    command_index = 0
    if preposition == '':
        #print(colorama.Fore.CYAN +'Single Entity Command')
        for i in package['contributes']['commands']:
            ext_entities,ext_actions,ext_prepositional = entity_action_recognizer('can you ' + i['title'],True)
            if(len(ext_entities)!=0 and len(ext_actions)!=0):
                if ext_prepositional == '' and entities[0]==ext_entities[0]:
                    #print(colorama.Fore.GREEN +' - Entity Matched with command [ ',i['title'],' ] at index ',command_index)
                    entity_match.add(command_index)
                if actions == ext_actions:
                    #print(colorama.Fore.GREEN +' - Action matched with command [ ',i['title'],' ] at index ',command_index)
                    action_match.add(command_index)
            command_index += 1
        packageFile.close()
        #print(colorama.Fore.GREEN +'Entities Matched Command Indexs: ',entity_match)
        #print(colorama.Fore.GREEN +'Action Matched Command Indexs: ',action_match)

        similar = list(action_match.intersection(entity_match))
        #print(colorama.Fore.GREEN +'Similar: ',similar)
        if len(similar) == 1:
            return package['contributes']['commands'][similar[0]]['command'],stemmer.stem(''.join(actions))+'ing ' + ' '.join(entities)
        #print('command not recognized.')
        return 'NULL','NULL'
    else:
        #print(colorama.Fore.CYAN +'Multi Entity Command. Preposition: ',preposition)
        for i in package['contributes']['commands']:
            ext_entities,ext_actions,ext_prepositional = entity_action_recognizer('can you ' + i['title'],True)
            if(len(ext_entities)!=0 and len(ext_actions)!=0):
                if ext_prepositional!='':
                        #print('entities[0]: ',entities[0],ext_entities[0])
                        #print('entities[1]',entities[1],ext_entities[1])
                        if (entities[0] == ext_entities[0] and entities[1] == ext_entities[1]):
                            #print(colorama.Fore.GREEN +' - Entity Matched with command [ ',i['title'],' ] at index ',command_index)
                            entity_match.add(command_index)
                if actions == ext_actions:
                    #print(colorama.Fore.GREEN +' - Action matched with command [ ',i['title'],' ] at index ',command_index)
                    action_match.add(command_index)
            command_index += 1
        packageFile.close()
        #print(colorama.Fore.CYAN +'Entities Matched Command Indexs: ',entity_match)
        #print(colorama.Fore.CYAN +'Action Matched Command Indexs: ',action_match)

        similar = list(action_match.intersection(entity_match))
        #print(colorama.Fore.GREEN +'Similar: ',similar)
        if len(similar) == 1:
            return package['contributes']['commands'][similar[0]]['command'],stemmer.stem(''.join(actions)) + 'ing ' + ' '.join(entities)
        #print('command not recognized.')
        return 'NULL','NULL'

def buildEntities(root_entities):
    #print('--building entities')
    combinations = []
    #print('Root Entities: ',root_entities)
    #root entities eg: ( (font,['word','text]),(size,['scale','length']), where [word,text] are root words for 'font
    if len(root_entities)>=2: #multi worded entity
          prefix_ent,pre_root = root_entities[0]
          post_ent,post_root = root_entities[1]
          for i in range(0,len(pre_root)):
              for j in range(0,len(post_root)):
                  combinations.append(pre_root[i]+ ' ' +post_root[j])
    elif len(root_entities)==1:
        prefix_ent,pre_root = root_entities[0]
        for i in range(0,len(pre_root)):
            combinations.append(pre_root[i])
    # elif len(root_entities)==0:
    #     combinations.append()
    #print('combos: ',combinations)
    return combinations

        


def test():
    # f = open('pos.txt','w')
    syns = syns_load()
    packageFile = open('package.json')
    package = json.load(packageFile)

    for i in package['contributes']['commands']:
        cmd = 'can you '+i['title']
        print('command: ',cmd)
        entities,actions,preposition = entity_action_recognizer(cmd,True)
        print("Entities: ",entities,' Actions:',actions, 'Preposition: ',preposition)
        known_entities = []
        new_entities = []
        for entity in entities:
            known_entities.append((entity,alternatives(syns,[entity])))
        for knw_ents in known_entities:
            #print('Known Entities after searching for root words: ',knw_ents[1])
            new_entities.append(knw_ents[1])
        #if root word for all the words describing an entity of are found
        # print(identify_command2(new_entities,actions,preposition))
def syn_test(sentence):
    from nltk.corpus import wordnet
    syns = syns_load()
    sentence = sentence.lower()
    tokens = nltk.word_tokenize(sentence)
    action = '' # only one verb per command ? change if accepting multiple commands
    default_pos_tags = nltk.pos_tag(tokens)
    print(default_pos_tags)
    entities,actions,preposition = entity_action_recognizer(sentence,True)
    print("Entities: ",entities,' Actions:',actions, 'Preposition: ',preposition)
    new_entities = []
    for entity in entities:
        new_entities.append(buildEntities(alternatives(syns,[entity])))
    print('entities to try with : ',new_entities)
    if preposition == '':
        print('Single Entity Command')
        
        new_entitis = new_entities[0]
        for new_entity in new_entitis:
            print('Trying with : ',new_entity)
            cmd,msg = identify_command2([new_entity],actions,preposition)
            if cmd!='NULL':
                print(msg)
               # break
    else:
        print('Multy Entity Command')
        new_entitis = []
        preceding_ents = new_entities[0]
        trailing_ents = new_entities[1]
        for i in range(0,len(preceding_ents)):
            for j in range(0,len(trailing_ents)):
                new_entitis.append([preceding_ents[i],trailing_ents[j]])
        for new_ents in new_entitis:
            print('Trying with :',new_ents)
            cmd,msg = identify_command2(new_ents,actions,preposition)
            if cmd != 'NULL':
                print(msg)
                break

        
        
#test()
# cmds = ['can you increase the texts size','can you get the texts under the cursor','can you insert a for loop']
# for cmd in cmds:
#     syn_test(cmd)
#     print('-------------------------------------------')
#     print()




        










