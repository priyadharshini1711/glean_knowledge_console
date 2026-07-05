import asyncio
from src.searcher import search

async def main():
    result = await search('engineering handbook rules')
    print('Status:', result.get('status'))
    print('Query:', result.get('query'))
    print('Total results:', result.get('total_results'))
    if result.get('status') == 'success':
        for i, r in enumerate(result.get('results', []), 1):
            print(f'\n[{i}] {r.get("title")}')
            print(f'    URL: {r.get("url")}')
            snippet = r.get('snippet', '')
            if len(snippet) > 100:
                print(f'    Snippet: {snippet[:100]}...')
            else:
                print(f'    Snippet: {snippet}')
    else:
        print('Error:', result.get('message'))

asyncio.run(main())
