"""One-off probe run on GitHub runners: checks CGV reachability and records
the site's XHR/fetch traffic so the schedule API can be reverse-engineered."""
import json, os, re, sys, time, urllib.request, urllib.error

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

def http(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.geturl(), dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, url, dict(e.headers), e.read()
    except Exception as e:
        return None, url, {}, repr(e).encode()

summary = {}
for i, url in enumerate([
    "https://www.cgv.co.kr/", "https://cgv.co.kr/", "https://m.cgv.co.kr/",
    "https://api.cgv.co.kr/", "http://www.cgv.co.kr/theaters/",
    "http://www.cgv.co.kr/reserve/show-times/",
    "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?areacode=01&theatercode=0056&date=20260930",
]):
    st, final, hdr, body = http(url)
    summary[url] = {"status": st, "final": final, "len": len(body), "server": hdr.get("Server")}
    open(f"{OUT}/http_{i}.html", "wb").write(body[:2_000_000])
    print(url, st, final, len(body), flush=True)
json.dump(summary, open(f"{OUT}/http_summary.json", "w"), ensure_ascii=False, indent=1)

# Browser capture of API traffic
from playwright.sync_api import sync_playwright
reqs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(user_agent=UA, locale="ko-KR", timezone_id="Asia/Seoul")
    page = ctx.new_page()
    def on_resp(resp):
        rq = resp.request
        if rq.resource_type not in ("xhr", "fetch"):
            return
        ent = {"url": rq.url, "method": rq.method, "status": resp.status,
               "req_headers": rq.headers, "post": rq.post_data}
        try:
            body = resp.text()
            ent["body"] = body[:300_000]
        except Exception as e:
            ent["body_err"] = repr(e)
        reqs.append(ent)
    page.on("response", on_resp)
    for name, url in [("home", "https://cgv.co.kr/"),
                      ("theater", "https://cgv.co.kr/cnm/cgvChart/theater"),
                      ("book", "https://cgv.co.kr/cnm/movieBook"),
                      ("oldtheaters", "http://www.cgv.co.kr/theaters/")]:
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception as e:
            print("goto fail", url, e, flush=True)
        time.sleep(3)
        open(f"{OUT}/page_{name}.html", "w").write(page.content())
        page.screenshot(path=f"{OUT}/page_{name}.png", full_page=False)
        # collect links for later exploration
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        open(f"{OUT}/links_{name}.txt", "w").write("\n".join(sorted(set(links))))
        print(name, page.url, len(reqs), flush=True)
    # save JS bundles list
    scripts = page.eval_on_selector_all("script[src]", "els => els.map(e => e.src)")
    open(f"{OUT}/scripts.txt", "w").write("\n".join(scripts))
    b.close()
json.dump(reqs, open(f"{OUT}/xhr.json", "w"), ensure_ascii=False, indent=1)
print("captured", len(reqs))
