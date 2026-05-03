from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import MediaFile
from django.core.files.base import ContentFile

from PIL import Image, ImageOps
import io
import os


# ─────────────────────────────────────────────────────────────────────────────
# WORDPRESS-STYLE IMAGE PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────
def process_image(uploaded_file, max_width=1920, max_height=1920, quality=82):
    """
    Kisi bhi image ko compress + resize karo WordPress ki tarah.
    content_type check nahi — extension se decide karo (reliable).
    """
    original_name = uploaded_file.name
    ext = os.path.splitext(original_name)[1].lower()
    name_without_ext = os.path.splitext(original_name)[0]

    # SVG aur GIF skip — as-is return karo
    if ext in ('.svg', '.gif'):
        uploaded_file.seek(0)
        return ContentFile(uploaded_file.read()), original_name

    # Image open karo — badi files ke liye bhi kaam karega
    uploaded_file.seek(0)
    try:
        # Pehle BytesIO mein load karo (large files ke liye safer)
        raw = io.BytesIO(uploaded_file.read())
        img = Image.open(raw)
        img.load()
    except Exception as e:
        # Open nahi ho sakti — original return karo
        uploaded_file.seek(0)
        return ContentFile(uploaded_file.read()), original_name

    # EXIF orientation fix (phone se aane wali photos seedhi hongi)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Resize agar zarurat ho (aspect ratio maintain hoga)
    orig_w, orig_h = img.size
    if orig_w > max_width or orig_h > max_height:
        img.thumbnail((max_width, max_height), Image.LANCZOS)

    # Format + mode decide karo
    if ext == '.png':
        # PNG — RGBA allowed, optimize
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        new_filename = name_without_ext + '.png'

    elif ext == '.webp':
        # WebP
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='WEBP', quality=quality, method=6)
        new_filename = name_without_ext + '.webp'

    else:
        # JPEG (jpg, jpeg, bmp, tiff — sab JPEG mein convert)
        if img.mode != 'RGB':
            # RGBA / P / LA → white background pe paste karo
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        new_filename = name_without_ext + '.jpg'

    buffer.seek(0)
    return ContentFile(buffer.read()), new_filename


# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────
def media_library_page(request):
    folder   = request.GET.get('folder', '')
    search   = request.GET.get('search', '')
    files_qs = MediaFile.objects.all()

    if folder:
        files_qs = files_qs.filter(folder=folder)
    if search:
        files_qs = files_qs.filter(name__icontains=search)

    paginator = Paginator(files_qs, 24)
    page      = request.GET.get('page', 1)
    files     = paginator.get_page(page)

    return render(request, 'media_library/library.html', {
        'files':          files,
        'folders':        MediaFile.FOLDER_CHOICES,
        'current_folder': folder,
        'search':         search,
        'total':          files_qs.count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# PICKER API
# ─────────────────────────────────────────────────────────────────────────────
def media_picker_api(request):
    folder   = request.GET.get('folder', '')
    search   = request.GET.get('search', '')
    page     = int(request.GET.get('page', 1))
    per_page = 20

    qs = MediaFile.objects.all()
    if folder:
        qs = qs.filter(folder=folder)
    if search:
        qs = qs.filter(name__icontains=search)

    total    = qs.count()
    start    = (page - 1) * per_page
    end      = start + per_page
    files    = qs[start:end]
    has_more = end < total

    return JsonResponse({
        'files': [
            {
                'id':     f.id,
                'url':    f.image.url if f.image else '',
                'name':   f.name or '',
                'size':   f.size_display,
                'folder': f.folder,
            }
            for f in files
        ],
        'has_more': has_more,
        'total':    total,
        'page':     page,
    })


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD API — Compression yahan hoti hai
# ─────────────────────────────────────────────────────────────────────────────
def media_upload_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    image  = request.FILES.get('image')
    folder = request.POST.get('folder', 'general')
    name   = request.POST.get('name', '')

    if not image:
        return JsonResponse({'error': 'No image provided'}, status=400)

    # Extension check (content_type browser pe depend karta hai — unreliable)
    allowed_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff')
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed_exts:
        return JsonResponse({'error': f'Invalid file type: {ext}'}, status=400)

    # Koi size limit nahi — compress hoke automatically chota ho jayega

    # ── COMPRESS + RESIZE ────────────────────────────────────────────────
    processed_file, new_filename = process_image(
        image,
        max_width=1920,
        max_height=1920,
        quality=82,
    )

    # ── DB SAVE ──────────────────────────────────────────────────────────
    clean_name = name or os.path.splitext(new_filename)[0]
    media = MediaFile(folder=folder, name=clean_name)
    media.image.save(new_filename, processed_file, save=True)
    # save=True automatically MediaFile.save() call karta hai
    # jo file_size bhi update kar deta hai

    return JsonResponse({
        'id':   media.id,
        'url':  media.image.url,
        'name': media.name,
        'size': media.size_display,
    })


# ─────────────────────────────────────────────────────────────────────────────
# DELETE API
# ─────────────────────────────────────────────────────────────────────────────
def media_delete_api(request, pk):
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'error': 'POST or DELETE only'}, status=405)

    media = get_object_or_404(MediaFile, pk=pk)
    media.delete()
    return JsonResponse({'success': True, 'id': pk})