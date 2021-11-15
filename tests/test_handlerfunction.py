from handlers import yamlHandlers

# Check callable status of yaml function
def test_callFirstLayerValue():
    resVal = yamlHandlers._parsing_yamlFile_omega(workflow_path="./", yamlfilename="dummy_config.yaml")
    assert resVal ['InputFolder']=='inputFolder/inputfile.txt'

def test_callSecondLayerValue():
    resVal = yamlHandlers._parsing_yamlFile_omega(workflow_path="./", yamlfilename="dummy_config.yaml")
    assert resVal['Output']['Path']=='outputFolder/'

def test_callParsingFunction():
    test_input = yamlHandlers._parsing_yamlFile(workflow_path=".", yamlfilename="dummy_config.yaml")
    resVal = yamlHandlers._reform_yamlFile("./", test_input, "dummy_created")
    with open("./dummy_config.yaml", "r") as testFile:
        with open(resVal, "r") as resultFile:
            testString = testFile.readlines()
            resultString = resultFile.readlines()
            assert len(testString)==len(resultString) # length test

            for i in range(0, len(testString)):
                assert testString[i].rstrip()==resultString[i].rstrip() # Line space and contents test
            
