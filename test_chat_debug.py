import asyncio
import sys
from src.chat import chat

async def main():
    try:
        print("Starting chat query...", flush=True)
        question = "What are the FY2026 roadmap milestones?"
        print(f"Question: {question}", flush=True)
        
        result = await chat(question)
        print(f"Result received: {type(result)}", flush=True)
        
        print(f"Status: {result.get('status')}")
        print(f"Question: {result.get('question')}\n")
        
        if result.get('status') == 'success':
            answer = result.get('answer', '')
            print("Answer:")
            print(answer)
            print("\n" + "="*80 + "\n")
            
            citations = result.get('citations', [])
            if citations:
                print("Sources:")
                for i, cite in enumerate(citations, 1):
                    print(f"[{i}] {cite.get('title')}")
                    if cite.get('url'):
                        print(f"    URL: {cite.get('url')}")
                    if cite.get('datasource'):
                        print(f"    Datasource: {cite.get('datasource')}")
            else:
                print("No sources cited.")
        else:
            print(f"Error: {result.get('message')}")
            if result.get('http_status'):
                print(f"HTTP Status: {result.get('http_status')}")
    except Exception as e:
        print(f"Exception occurred: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
