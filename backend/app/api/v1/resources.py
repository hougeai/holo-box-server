from fastapi import APIRouter, Query
from fastapi import File, UploadFile, Form
from tortoise.expressions import Q
from controllers import (
    ota_controller,
)
from schemas.base import Fail, Success, SuccessExtra
from schemas.resource import (
    OtaCreate,
    OtaUpdate,
)
from core.minio import oss


router = APIRouter()


# OTA相关API
@router.get('/ota/list', summary='查看ota列表')
async def list_ota(
    page: int = Query(1, description='页码'),
    page_size: int = Query(10, description='每页数量'),
    app_version: str = Query('', description='版本号，用于搜索'),
    chip_type: str = Query('', description='芯片类型，用于搜索'),
    device_model: str = Query('', description='设备型号，用于搜索'),
):
    q = Q()
    if app_version:
        q &= Q(appVersion__contains=app_version)
    if chip_type:
        q &= Q(chipType__contains=chip_type)
    if device_model:
        q &= Q(deviceModel__contains=device_model)
    # 当前页码 每页显示数量；返回的是总数和当前页数据列表
    total, objs = await ota_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/ota/create', summary='创建ota')
async def create_ota(obj_in: OtaCreate):
    obj = await ota_controller.get_by_name(app_version=obj_in.app_version, device_model=obj_in.device_model)
    if obj:
        return Fail(code=400, msg='ota版本已存在')
    await ota_controller.create(obj_in=obj_in)
    return Success(msg='Created Successfully')


@router.post('/ota/update', summary='更新ota')
async def update_ota(obj_in: OtaUpdate):
    await ota_controller.update(id=obj_in.id, obj_in=obj_in)
    return Success(msg='Updated Successfully')


@router.delete('/ota/delete', summary='删除ota')
async def delete_ota(id: int = Query(..., description='ID')):
    # 先删除OSS上的相关文件
    obj = await ota_controller.get(id=id)
    if obj.ota_url:
        await oss.delete_file_async(key=obj.ota_url)
    if obj.whole_url:
        await oss.delete_file_async(key=obj.whole_url)
    await ota_controller.remove(id=id)
    return Success(msg='Deleted Successfully')


@router.post('/ota/file', summary='上传ota文件到oss')
async def upload_file_ota(
    file: UploadFile = File(...),
    app_version: str = Form(...),
    device_model: str = Form(...),
    file_type: str = Form(...),
):
    url = f'{device_model}-{app_version}.{file_type}'
    file_content = await file.read()
    status = await oss.upload_file_async(key=f'firmware/pro/{url}', file_data=file_content)
    if not status:
        return Fail(code=500, msg='固件文件上传失败')
    return Success(data={'url': f'firmware/pro/{url}'})
