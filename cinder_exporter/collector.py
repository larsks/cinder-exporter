import logging
import re

from prometheus_client.core import (
    GaugeMetricFamily,
    InfoMetricFamily,
)

LOG = logging.getLogger(__name__)
re_invalid_chars = re.compile(r'[^\w]+')


class CinderCollector(object):
    def __init__(self, cloud):
        self.cloud = cloud

    def volumes(self):
        endpoint = self.cloud.endpoint_for('volume')
        url = '{}/volumes/detail'.format(endpoint)
        res = self.cloud.session.get(url, params={'all_tenants': 'true'})
        res.raise_for_status()
        return res.json().get('volumes', [])

    def get_volume_metrics(self):
        vol_info = GaugeMetricFamily(
            'cinder_volume_info',
            'Info about a volume',
            labels=[
                'cinder_vol_uuid', 'cinder_vol_name', 'cinder_vol_type',
                'cinder_vol_bootable', 'cinder_vol_status',
                'os_project_uuid', 'os_user_uuid',
            ])
        vol_size = GaugeMetricFamily(
            'cinder_volume_size_gb',
            'Size of a volume',
            labels=['cinder_vol_uuid'])

        for vol in self.volumes():
            LOG.debug('getting information for volume %s', vol['id'])
            vol_info.add_metric([
                vol['id'], vol['name'], vol['volume_type'], vol['bootable'],
                vol['status'],
                vol['os-vol-tenant-attr:tenant_id'],
                vol['user_id'],
            ], 1.0)
            vol_size.add_metric([vol['id']], vol['size'])

        yield vol_info
        yield vol_size

    def describe(self):
        return []

    def collect(self):
        LOG.info('start collecting volume information')
        yield from self.get_volume_metrics()
        LOG.info('done collecting volume information')
