def clean_url(url):
    return url[:-1] if url.endswith('/') else url