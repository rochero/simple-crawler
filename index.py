from template._example import crawl
from utils.tool import load_txt

if __name__ == '__main__':
    lis = [x[0] for x in load_txt('./data/example/url.txt')]
    save_path='./data/example/result.xlsx'
    crawl(lis,save_path, chunk_size=100, max_workers = 4)
