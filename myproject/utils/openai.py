import openai

def get_openai_response(model="gpt-3.5-turbo", system_message="", user_messages=None, max_tokens=100):
    """
    Generates a response using OpenAI's GPT-based model.
    
    Parameters:
        model (str): The name of the OpenAI model to use. Default is "gpt-3.5-turbo".
        system_message (str): The system-level instruction for the model.
        user_messages (list): A list of dictionaries containing the user conversation history.
                              Example: [{"role": "user", "content": "Hello, how are you?"}]
        max_tokens (int): The maximum number of tokens for the response. Default is 100.
    
    Returns:
        str: The response content from the OpenAI API.
    """
    if user_messages is None:
        user_messages = []

    # Prepare the message structure
    messages = [{"role": "system", "content": system_message}] + user_messages

    try:
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"