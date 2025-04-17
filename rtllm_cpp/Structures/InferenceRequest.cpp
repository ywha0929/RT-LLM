#include <iostream>
#include <string>

using namespace std;
class InferenceRequest
{
    private:
        bool createCacheMode;
        string input;
        string cacheFileName;
        int client;
        string addr;
        int requestID;
        int priority;
        int prevOutput;
    public :
        InferenceRequest(bool createCacheMode,string input,string cacheFileName, int client, string addr, int requestID, int priority, int prevOutput) {
            createCacheMode= createCacheMode
        }
}