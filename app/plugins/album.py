from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import RedirectResponse


UPLOAD_FOLDER = Path("images")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def album_uploade_page():
    files = list(UPLOAD_FOLDER.glob("*"))
    file_urls = [f"/album/images/{file.name}" for file in files]

    html_content = f"""
    <html>
        <head>
            <title>Image Upload</title>
            <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h2 class="mb-4">Upload an Image</h2>
                <form action="/album/upload-image/" method="post" enctype="multipart/form-data" class="mb-4">
                    <div class="form-group">
                        <input type="file" name="file" class="form-control-file">
                    </div>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </form>
                <h2 class="mb-4">Uploaded Images</h2>
                <div class="row">
                    {"".join(f'''
                        <div class="col-md-3 mb-3">
                            <div class="card">
                                <img src="{url}" class="card-img-top" alt="{file.name}">
                                <div class="card-body text-center">
                                    <form action="/album/delete-image/" method="post">
                                        <input type="hidden" name="filename" value="{file.name}">
                                        <button type="submit" class="btn btn-danger">Delete</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    ''' for file, url in zip(files, file_urls))}
                </div>
            </div>
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        </body>
    </html>
    """
    return html_content


def upload_image(file):
    # Generate timestamp and construct new filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    extension = Path(file.filename).suffix
    new_filename = f"{timestamp}{extension}"
    file_location = UPLOAD_FOLDER / new_filename
    with file_location.open("wb") as buffer:
        buffer.write(file.file.read())
    return RedirectResponse(url="/album/admin", status_code=303)


def delete_image(filename: str):
    file_location = UPLOAD_FOLDER / filename
    if file_location.exists():
        file_location.unlink()
        return RedirectResponse(url="/album/admin", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="File not found")


def get_data():
    files = list(UPLOAD_FOLDER.glob("*"))
    file_urls = [f"/album/images/{file.name}" for file in files]
    return {"images": file_urls}
