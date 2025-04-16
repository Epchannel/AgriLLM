import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import time
import re

base_url = "https://vaas.org.vn/kienthuc/Caylua/"
main_url = base_url + "index.htm"
output_dir = "vaas_crawled_data"
output_file = os.path.join(output_dir, "cay_lua_full_content.txt")

# Tạo thư mục đầu ra nếu chưa tồn tại
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Danh sách các URL đã crawl để tránh crawl lặp lại
crawled_urls = set()

# Hàm để làm sạch văn bản
def clean_text(text):
    # Loại bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    # Loại bỏ các ký tự đặc biệt không cần thiết
    text = re.sub(r'[^\w\s.,;:?!()"-]', '', text)
    return text

# Mở file để ghi nội dung
def open_output_file():
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TỔNG HỢP NỘI DUNG VỀ CÂY LÚA TỪ VAAS.ORG.VN\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Nguồn: {base_url}\n")
        f.write(f"Thời gian crawl: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=" * 80 + "\n\n")

# Hàm để ghi nội dung vào file
def write_to_file(title, url, content, level=1):
    with open(output_file, 'a', encoding='utf-8') as f:
        # Tạo định dạng tiêu đề dựa trên level
        header_marker = "#" * level
        separator = "-" * 80 if level == 1 else "." * 80
        
        f.write(f"\n{separator}\n")
        f.write(f"{header_marker} {title}\n")
        f.write(f"URL: {url}\n")
        f.write(f"{separator}\n\n")
        f.write(content + "\n\n")

# Hàm để crawl nội dung của một trang cụ thể
def crawl_page(url, depth=0, max_depth=3, level=1):
    # Kiểm tra nếu URL đã được crawl
    if url in crawled_urls:
        print(f"Đã crawl URL này rồi: {url}")
        return []
    
    # Thêm URL vào danh sách đã crawl
    crawled_urls.add(url)
    
    print(f"Đang crawl [{depth}/{max_depth}]: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Lấy tiêu đề trang
            title = soup.title.text if soup.title else "Không có tiêu đề"
            print(f"Tiêu đề: {title}")
            
            # Lấy nội dung chính
            content = ""
            
            # Thử tìm nội dung trong các thẻ phổ biến
            content_div = soup.find('div', class_='content') or soup.find('div', id='content')
            if content_div:
                content = content_div.get_text(strip=True)
            else:
                # Nếu không tìm thấy div cụ thể, lấy toàn bộ văn bản từ body
                body = soup.find('body')
                if body:
                    # Loại bỏ các thẻ script và style
                    for script in body(["script", "style"]):
                        script.extract()
                    content = body.get_text(strip=True)
            
            # Làm sạch nội dung
            content = clean_text(content)
            
            # Ghi nội dung vào file
            write_to_file(title, url, content, level)
            
            # Nếu chưa đạt đến độ sâu tối đa, tiếp tục crawl các liên kết con
            if depth < max_depth:
                # Tìm các liên kết con trong trang này
                links = soup.find_all('a')
                sub_links = []
                
                for link in links:
                    href = link.get('href')
                    if href and not href.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
                        # Đây là liên kết nội bộ
                        full_url = urllib.parse.urljoin(url, href)
                        
                        # Chỉ crawl các URL thuộc base_url
                        if full_url.startswith(base_url):
                            link_text = link.get_text(strip=True)
                            sub_links.append((link_text, full_url))
                            
                            # Crawl ngay liên kết con này
                            time.sleep(0.5)  # Tạm dừng để không gây tải cho server
                            crawl_page(full_url, depth + 1, max_depth, level + 1)
                
                return sub_links
        else:
            print(f"Không thể truy cập {url}. Mã phản hồi: {response.status_code}")
    
    except Exception as e:
        print(f"Lỗi khi crawl {url}: {e}")
    
    return []

# Hàm chính để bắt đầu crawl từ trang chủ
def start_crawling():
    print("BẮT ĐẦU CRAWL TOÀN BỘ TRANG KIENTHUC/CAYLUA")
    print("=" * 50)
    
    # Tạo file đầu ra
    open_output_file()
    
    # Crawl trang chủ và tất cả các trang con
    crawl_page(main_url)
    
    # Thêm thông tin tổng kết vào cuối file
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write("KẾT THÚC TÀI LIỆU\n")
        f.write(f"Tổng số trang đã crawl: {len(crawled_urls)}\n")
        f.write("=" * 80 + "\n")
    
    print("\nĐÃ HOÀN THÀNH CRAWL!")
    print(f"Tổng số trang đã crawl: {len(crawled_urls)}")
    print(f"Dữ liệu được lưu trong file: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    start_crawling()
