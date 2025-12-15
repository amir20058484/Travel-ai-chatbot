import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage, ChatCompletion
from prompts import get_system_prompt
from src.tools import SafarTools

class AgentManager:
    """
    Core LLM-based orchestrator agent for Safar Travel.
    Handles conversation state, tool calling, and response generation.
    """

    def __init__(self, model_name: str, api_key: str, base_url: str):
        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0 
        )
        
        self.tools = SafarTools(self.client, self.model_name)
        
        self.tool_callables = self.tools.get_tool_callables()
        
        self.tool_schemas = self.tools.get_tool_schemas()

        self.openai_tools_specs = [{"type": "function", "function": func_schema} for func_schema in self.tool_schemas]
        
        self.history: List[Dict] = [ 
            {"role": "system", "content": get_system_prompt()}
        ]
        
        print("DEBUG: AgentManager initialized. RAG data loaded. Tools prepared.")
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single function call based on the LLM's request."""
        function_name = tool_call["function"]["name"]
        
        func_map = {f.__name__: f for f in self.tool_callables} 
        function_to_call = func_map.get(function_name)

        if not function_to_call:
            return {"status": "error", "message": f"Unknown function: {function_name}"}

        try:
            function_args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return {"status": "error", "message": f"Error decoding JSON arguments for {function_name}"}

        print(f"DEBUG: Executing tool: {function_name} with args: {function_args}")
        tool_output = function_to_call(**function_args)
        
        return tool_output

    def process_message(self, user_message: str) -> str:
        """
        Main entry point for processing a user message.
        Handles the conversational loop including tool orchestration.
        """
        
        self.history.append({"role": "user", "content": user_message})
        messages_to_send = self.history
        
        for _ in range(5):
            
            try:
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages_to_send,
                    tools=self.openai_tools_specs,
                    tool_choice="auto", 
                )
            except Exception as e:
                error_msg = f"متاسفانه در حال حاضر امکان برقراری ارتباط با سیستم وجود ندارد. لطفا کمی بعد دوباره تلاش کنید. (An API error occurred: {str(e)})"
                self.history.pop() 
                return error_msg
                
            model_response: ChatCompletionMessage = response.choices[0].message
            
            if model_response.content:
                final_response = model_response.content
                self.history.append({"role": "assistant", "content": final_response})
                
                return final_response

            elif model_response.tool_calls:

                messages_to_send.append(model_response.model_dump()) 

                tool_outputs: List[Dict[str, Any]] = []
                for tool_call in model_response.tool_calls:

                    tool_result = self._execute_tool_call(tool_call.model_dump()) 
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": json.dumps(tool_result, ensure_ascii=False) 
                    })
                
                messages_to_send.extend(tool_outputs)
                
                continue
                
            else:
                fallback_msg = "متاسفانه نتوانستم درخواست شما را متوجه شوم. آیا میتوانید واضح تر توضیح دهید؟ (I could not understand your request. Can you explain more clearly?)"
                self.history.pop() 
                return fallback_msg
                
        return "Sorry, I reached the maximum number of internal steps. Could you please simplify your request?"