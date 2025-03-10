# using RTLLM 250213
import torch
from transformers import AutoTokenizer, LlamaForCausalLM
from transformers.cache_utils import DynamicCache, Cache, StaticCache
from typing import Optional
import copy
import inspect
from torch.profiler import profile, record_function, ProfilerActivity
import gc
import json


class Answerer:
    def __init__(self,model_name,tokenizer_name):
        self.model = LlamaForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16,
                                                      attn_implementation="flash_attention_2")
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, torch_dtype=torch.float16)
        self.device = 'cuda'
        self.model.to(self.device)
        self.kvCacheDir = '/home/ywha/RT-LLM/kvCaches/'
        # self.emergencyCache = DynamicCache.from_legacy_cache(
        #     torch.load('/home/ywha/LLMTest/RTLLM/KVCacheForEmergency.pt')).to(self.device)

    def ask(self, question, emergency=False, count=1000, cacheFileName:str=None,historyFileName:str=None):
        with open( self.kvCacheDir+historyFileName, "r", encoding="utf-8") as f:
            input = json.load(f)
        f.close()
        input.append({'role':'user','content':question})
        past_key_values = torch.load( self.kvCacheDir+cacheFileName, map_location=self.device)
        print(past_key_values)
        if emergency == False:  # no emergency mode
            if past_key_values == None:
                generated_ids = self.model.talk(question=input, tokenizer=self.tokenizer, count=count,
                                            emergency=emergency)
                output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True,
                                                     clean_up_tokenization_spaces=False)
            else :
                generated_ids = self.model.talk(question=input, tokenizer=self.tokenizer, count=count,
                                                emergency=emergency, Cache=past_key_values)
                output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True,
                                                     clean_up_tokenization_spaces=False)
                input.append({'role':'assistant','content':output})
                self.saveHistory(
                                 historyFilename=historyFileName,
                                 cacheFilename=cacheFileName,
                                 history=input,
                                 kvCache=past_key_values
                                 )

            # print(generated_ids)

            # print(output)
            return ''.join(output), len(output)
        else :
            if past_key_values==None:
                generated_ids = self.model.talk(question=input, tokenizer=self.tokenizer, count=count,
                                                emergency=emergency, Cache=None)
                output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True,
                                                     clean_up_tokenization_spaces=False)
            else :
                generated_ids = self.model.talk(question=input, tokenizer=self.tokenizer, count=count,
                                                emergency=emergency, Cache=past_key_values)
                output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True,
                                                     clean_up_tokenization_spaces=False)
                input.append({'role': 'assistant', 'content': output})
                self.saveHistory(
                                 historyFilename=historyFileName,
                                 cacheFilename=cacheFileName,
                                 history=input,
                                 kvCache=past_key_values
                                 )


            # print(output)
            return ''.join(output), len(output)

    def saveHistory(self,historyFilename,cacheFilename,history,kvCache):

        with open( self.kvCacheDir+historyFilename, "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
            json.dump(history, f)  # json.dump를 이용하여 쓰기
        torch.save(kvCache,  self.kvCacheDir+cacheFilename)

    def createKVCache(self,historyFileName):
        jsonFilename = self.kvCacheDir+historyFileName+'.json'
        history = [{"role": "assistant", "content": "You are a chatbot who answers my question."}]
        with open(jsonFilename, "w", encoding="utf-8") as f:  # 쓰기 모드(w)나 추가 모드(a)로 열기
            json.dump(history, f)  # json.dump를 이용하여 쓰기

        kvCache = DynamicCache()
        with open(jsonFilename, "r", encoding="utf-8") as f:
            history = json.load(f)
        encoded_input = self.tokenizer.apply_chat_template(history,return_dict=True,return_tensors='pt').to(self.device)
        output = self.model(**encoded_input,past_key_values=kvCache)
        cacheFileName = jsonFilename[:-5] + '.pt'
        torch.save(kvCache, cacheFileName)