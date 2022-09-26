import uvicorn

if __name__ == '__main__':
    uvicorn.run('c3api:app', host='0.0.0.0', port = 8000)
