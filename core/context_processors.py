from core.models import PoolConfiguration


def pool_config(request):
    return {"pool_config": PoolConfiguration.get_solo()}

