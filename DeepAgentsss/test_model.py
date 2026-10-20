import os
import time
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
# Ensure your free API key is configured in your environment
# os.environ["GROQ_API_KEY"] = "gsk_..."

def test_groq_models():
    # Initialize client (uses GROQ_API_KEY environment variable natively)
    try:
        client = Groq()
    except Exception as e:
        print(f"❌ Initialization Failed: Ensure GROQ_API_KEY environment variable is set. Error: {e}")
        return

    # Updated collection of active 2026 production and preview endpoints
    model_suite = {
        "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b",
        "OpenAI GPT-OSS 120B": "openai/gpt-oss-120b",
        "Meta Llama 3.1 8B (Legacy Alias)": "llama-3.1-8b-instant",
        "Meta Llama 3.3 70B (Legacy Alias)": "llama-3.3-70b-versatile",
        "Alibaba Qwen 3.8 27B (Multimodal)": "qwen/qwen3.8-27b"
    }

    print("==================================================")
    print("      🚀 STARTING GROQ FREE-TIER MODEL MATRIX TEST")
    print("==================================================\n")

    for friendly_name, model_id in model_suite.items():
        print(f"📡 Testing model: {friendly_name} [{model_id}]...")
        
        try:
            start_time = time.time()
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": "Respond with the single word: 'Success'"}
                ],
                max_tokens=10,
                temperature=0.0
            )
            elapsed_time = time.time() - start_time
            response_text = completion.choices[0].message.content.strip()
            
            print(f"  ✅ SUCCESS | Response: '{response_text}' | Latency: {elapsed_time:.2f}s")
            
        except Exception as e:
            # Captures specific issues like Bad Requests (400) or Rate Limits (429)
            print(f"  ❌ FAILED  | Error: {str(e).splitlines()[0]}")
        
        # Free Tier Precaution: Wait 2 seconds between invocations to prevent RPM (Requests Per Minute) locks
        time.sleep(2)

    print("\n==================================================")
    print("      🏁 MATRIX TEST COMPLETION")
    print("==================================================")

if __name__ == "__main__":
    test_groq_models()
