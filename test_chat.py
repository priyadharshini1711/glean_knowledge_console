import asyncio
from src.chat import chat

async def main():
    question = "What are the FY2026 roadmap milestones?"
    result = await chat(question)
    
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

asyncio.run(main())
