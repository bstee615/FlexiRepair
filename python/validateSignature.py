import os
from common.commons import *
DATA_PATH = os.environ["DATA_PATH"]
ROOT_DIR = os.environ["ROOT_DIR"]
DATASET = os.environ["dataset"]
COCCI_PATH = join(os.environ["coccinelle"],'spatch')
DATASET_PATH = os.environ["SIGNATURES_PATH"]

VALID_LIST = os.environ["VALID_LIST"]
VALID_TYPE = os.environ["VALID_TYPE"]
PRIORITIZION = os.environ["PRIORITIZION"]
def patchSourceFile(bugPath,spfile,bugName):

    srcPath = bugPath
    patchName = bugName

    if(isfile(join(DATASET_PATH,bugName,'patched',patchName+spfile+'.c'))):
        return join(DATASET_PATH,bugName,'patched',patchName+spfile+'.c')

    if not (isfile(join(DATASET_PATH,bugName,'patches',patchName+spfile+'.txt'))):
        cmd = COCCI_PATH + ' --sp-file ' + join(DATASET, 'cocci', spfile) + ' ' + srcPath + ' --patch -o' + join(
            DATASET_PATH, bugName, 'patches', patchName) + ' > ' + join(DATASET_PATH, bugName,
                                                                                   'patches',
                                                                                   patchName + spfile + '.txt')

        output, e = shellGitCheckout(cmd)
    # logging.info(output)
    patchSize = os.path.getsize(join(DATASET_PATH,bugName,'patches',patchName+spfile+'.txt'))
    if patchSize == 0 :
        # os.remove(join(DATA_PATH,"introclass",bugName,'patches',patchName+spfile+'.txt'))
        return None
    else:

        cmd = 'patch -d '+'/'.join(srcPath.split('/')[:-1])+' -i '+join(DATASET_PATH,bugName,'patches',patchName+spfile+'.txt')+' -o '+join(DATASET_PATH,bugName,'patched',patchName+spfile+'.c')
        o,e = shellGitCheckout(cmd)
        return join(DATASET_PATH, bugName, 'patched', patchName + spfile + '.c')

def validateCore(t):
    bugName,isHeldout,prioritize = t

    if not os.path.exists(join(DATASET_PATH, bugName, 'patches')):
        os.makedirs(join(DATASET_PATH, bugName, 'patches'))
    if not os.path.exists(join(DATASET_PATH, bugName, 'patched')):
        os.makedirs(join(DATASET_PATH, bugName, 'patched'))

    fix = 'failure'
    output = ''

    output += 'bugName:' + bugName + ', '

    spfiles = load_zipped_pickle(join(DATA_PATH, 'uPatterns.pickle'))

    # Add column mapping project index to project name
    spfiles['uProjects'] = spfiles.uFiles.apply(lambda x: list(set([i.split('/{')[0].replace('(','') for i in x])))
    # Get only patterns which were not inferred from codeflaws
    # spfiles = spfiles[~spfiles.uProjects.apply(lambda x: np.all([i == 'codeflaws' for i in x]))]
    # TODO: Get only patterns which were not inferred from this signature's source project
    spfiles.sort_values(by=prioritize,inplace=True,ascending=False)

    cmd = 'make -C ' + join(DATASET_PATH, bugName) + ' clean'
    o, e = shellGitCheckout(cmd)

    for idx, spfile in enumerate(spfiles.uid.values.tolist()):
        if spfile == '.DS_Store':
            continue

        buggyFileName = 'main.c'
        path = join(DATASET_PATH,bugName,buggyFileName)
        patch = patchSourceFile(path, spfile, bugName)

        times = 0
        if patch is None:
            continue

        shutil.copy2(path, path+'.bak') # Backup main.c
        dest = join(DATASET_PATH, bugName)
        shutil.copy2(patch, dest) # Copy patched file
        shutil.copy2(dest, path) # Replace main.c with patched file

        cmd = 'make -C ' + join(DATASET_PATH, bugName) + ' main'
        o, e = shellGitCheckout(cmd)

        if not e:
            # cmd = 'mv ' + join(DATASET_PATH,bugName,bugName+spfile) + ' ' + join(DATASET_PATH,bugName,contestid+'-'+problem+'-'+buggyId)
            # o, e = shellGitCheckout(cmd)

            output += '@True:' + str(idx) + ':' + patch.split('/')[-1] + '@'
            # validTests = getTestList(join(DATASET_PATH, bugName),isHeldout)

            # post_failure_cases, post_failure, total = test_all(join(DATASET_PATH, bugName, contestid+'-'+problem+'-'+buggyId), validTests, join(DATASET_PATH, bugName))

            # cmd = f'cd {join(DATASET_PATH, bugName)} && timeout 5m bash val.sh'
            # o, e = shellGitCheckout(cmd)

            # output += str(post_failure) + ' '
            # if post_failure == 0:
            #     times += 1
            #     fix = 'success'
            #     output += 'fix {} by {} '.format(bugName, patch)
            #     break

    # output += 'times:{}, '.format(times) + fix
    # print(output)
    return output


def validate():

     bugs2test = listdir(DATASET_PATH)
     # Filter out irrelevant paths
     bugs2test = [b for b in bugs2test if not(b == '.DS_Store' or b == 'README.md' or b.endswith('.txt') or b.endswith('.tar.gz'))]
     bugs2test.sort()
     if validList != ['ALL']:
         bugs2test = [b for b in bugs2test if b in validList]


     isHeldout = True
     if VALID_TYPE == 'black':
         isHeldout = False
     validList = VALID_LIST.split(',')



     prioritize = ''
     if PRIORITIZION == 'project':
         prioritize = 'uProject'
     elif PRIORITIZION == 'patch':
         prioritize = 'uPatch'
     elif PRIORITIZION == 'file':
         prioritize = 'uFilenames'
     elif PRIORITIZION == 'function':
         prioritize = 'uFunction'
     elif PRIORITIZION == 'hunk':
         prioritize = 'uFreq'
     else:
        raise Exception("Unknown PRIORITIZION " +PRIORITIZION)
        return

     bugList = []
     for b in bugs2test:
        t = b,isHeldout,prioritize
        bugList.append(t)

     output = validateCore(bugList[0])  # TODO: This is just test
     print(output)
     # results = parallelRunMerge(testCore, bugList,max_workers=10)
    #  results = parallelRunMerge(validateCore, bugList)
    #  print('\n'.join(results))
    #  dest = join(DATA_PATH, 'sigResults'+PRIORITIZION+VALID_TYPE)
    #  print('Validation results save to :' + dest)
    #  with open(dest, 'w', encoding='utf-8') as writeFile:
    #      writeFile.write('\n'.join(results))
