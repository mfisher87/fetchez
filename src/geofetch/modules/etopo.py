#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
geofetch.modules.etopo
~~~~~~~~~~~~~~~~~~~~~~

Fetch ETOPO 2022 Global Relief Model data from NOAA NCEI.

ETOPO 2022 is available in:
**15 arc-second tiles:** (Approx 450m) Tiled in 15x15 degree chunks. 
This module indexes these into FRED for region-based retrieval.

**30 & 60 arc-second:** (Approx 900m & 1800m) Global single files.

:copyright: (c) 2022 - 2026 Regents of the University of Colorado
:license: MIT, see LICENSE for more details.
"""

import logging
from typing import Optional, Dict

from geofetch import core
from geofetch import utils
from geofetch import fred
from geofetch import cli

logger = logging.getLogger(__name__)

ETOPO_BASE_URL_15S_GTIF = 'https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/'
ETOPO_BASE_URL_15S_NC = 'https://www.ngdc.noaa.gov/thredds/fileServer/global/ETOPO2022/15s/'
ETOPO_BASE_URL_30S_GTIF = 'https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/'
ETOPO_BASE_URL_60S_GTIF = 'https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/'
ETOPO_METADATA_URL = 'https://data.noaa.gov/metaview/page?xml=NOAA/NESDIS/NGDC/MGG/DEM//iso/xml/etopo_2022.xml&view=getDataView&header=none'

# Map resolutions to their base URLs and available types
ETOPO_URLS = {
    '15s': {
        'bed': f'{ETOPO_BASE_URL_15S_GTIF}15s_bed_elev_gtif/',
        'bed_sid': f'{ETOPO_BASE_URL_15S_GTIF}15s_bed_sid_gtif/',
        'surface': f'{ETOPO_BASE_URL_15S_GTIF}15s_surface_elev_gtif/',
        'surface_sid': f'{ETOPO_BASE_URL_15S_GTIF}15s_surface_sid_gtif/',
    },
    '30s': {
        'bed': f'{ETOPO_BASE_URL_30S_GTIF}30s_bed_elev_gtif/ETOPO_2022_v1_30s_N90W180_bed.tif',
        'surface': f'{ETOPO_BASE_URL_30S_GTIF}30s_surface_elev_gtif/ETOPO_2022_v1_30s_N90W180_surface.tif',
    },
    '60s': {
        'bed': f'{ETOPO_BASE_URL_60S_GTIF}60s_bed_elev_gtif/ETOPO_2022_v1_60s_N90W180_bed.tif',
        'surface': f'{ETOPO_BASE_URL_60S_GTIF}60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif',
    }
}

NETCDF_BASE_URLS = {
    'bed': f'{ETOPO_BASE_URL_15S_NC}15s_bed_elev_netcdf/',
    'bed_sid': f'{ETOPO_BASE_URL_15S_NC}15s_bed_sid_netcdf/',
    'surface': f'{ETOPO_BASE_URL_15S_NC}15s_surface_elev_netcdf/',
    'surface_sid': f'{ETOPO_BASE_URL_15S_NC}15s_surface_sid_netcdf/',
}

# =============================================================================
# ETOPO Module
# =============================================================================
@cli.cli_opts(
    help_text="ETOPO 2022 Global Relief Model",
    resolution="Resolution: '15s' (Tiled), '30s' (Global), '60s' (Global). Default: 15s",
    datatype="Data Type: 'bed', 'surface', 'bed_sid', 'surface_sid'. Default: bed",
    format="File Format: 'gtif' or 'netcdf'. Default: gtif",
    update="Force update of the local index (FRED)"
)

class ETOPO(core.FetchModule):
    """Fetch ETOPO 2022 data.
    
    The ETOPO Global Relief Model integrates topography, bathymetry, and 
    shoreline data.
    """
    
    def __init__(self, 
                 resolution: str = '15s', 
                 datatype: str = 'bed', 
                 format: str = 'gtif',
                 update: bool = False,
                 **kwargs):
        super().__init__(name='etopo', **kwargs)
        self.resolution = resolution if resolution in ETOPO_URLS else '15s'
        self.datatype = datatype
        self.file_format = format
        self.force_update = update

        # Only initialize FRED if we are using the tiled 15s dataset
        if self.resolution == '15s':
            self.fred = fred.FRED(name='etopo')
            if self.force_update or len(self.fred.features) == 0:
                self.update_index()

                
    def update_index(self):
        """Crawl the ETOPO 15s directories and update the FRED index."""
        
        logger.info("Updating ETOPO 15s Index from NOAA...")
        
        self.fred.features = [] # Clear existing
        count = 0
        
        # We iterate through the GeoTIFF directories to find valid tiles.
        # If a tile exists as GeoTIFF, it also exists as NetCDF.
        for dtype, url in ETOPO_URLS['15s'].items():
            page = core.Fetch(url).fetch_html()
            if page is None:
                logger.warning(f"Failed to access {url}")
                continue
                
            rows = page.xpath('//a[contains(@href, ".tif")]/@href')
            
            for row in rows:
                filename = row.split('/')[-1] # e.g. ETOPO_2022_v1_15s_N90W180_bed.tif
                sid = filename.split('.')[0]
                
                try:
                    # ETOPO naming convention, N90W180, is the Top-Left corner
                    parts = sid.split('_')
                    
                    # Find the part that looks like N90W180
                    spat = next((p for p in parts if ('N' in p or 'S' in p) and ('E' in p or 'W' in p)), None)
                    if not spat: continue

                    # Split N90W180 -> N90, W180
                    xsplit = 'E' if 'E' in spat else 'W'
                    ysplit = 'S' if 'S' in spat else 'N'
                    
                    parts_geo = spat.split(xsplit)
                    y_str = parts_geo[0].split(ysplit)[-1] # 90
                    x_str = parts_geo[-1] # 180
                    
                    x = int(x_str)
                    y = int(y_str)

                    if xsplit == 'W': x = -x
                    if ysplit == 'S': y = -y

                    # 15s tiles are 15x15 degrees.
                    w, e = x, x + 15
                    n, s = y, y - 15
                    
                    geom = {
                        "type": "Polygon",
                        "coordinates": [[
                            [w, s], [e, s], [e, n], [w, n], [w, s]
                        ]]
                    }

                    # Add GeoTIFF Entry
                    self.fred.add_survey(
                        geom=geom,
                        Name=sid,
                        ID=sid,
                        Agency='NOAA',
                        DataLink=f"{url}{row}",
                        DataType=dtype,
                        DataFormat='gtif',
                        Date='2022',
                        Info='ETOPO 2022 (15s GeoTIFF)'
                    )
                    
                    # Add NetCDF Entry (constructed URL)
                    nc_base = NETCDF_BASE_URLS.get(dtype)
                    if nc_base:
                        nc_name = f"{sid}.nc"
                        self.fred.add_survey(
                            geom=geom,
                            Name=f"{sid}_nc",
                            ID=sid,
                            Agency='NOAA',
                            DataLink=f"{nc_base}{nc_name}",
                            DataType=dtype,
                            DataFormat='netcdf',
                            Date='2022',
                            Info='ETOPO 2022 (15s NetCDF)'
                        )
                    count += 1
                    
                except (ValueError, IndexError) as e:
                     logger.debug(f"Failed to parse ETOPO filename {filename}: {e}")
                    continue

        logger.info(f"Indexed {count} ETOPO 15s datasets.")
        self.fred.save()

        
    def run(self):
        """Run the ETOPO fetching module."""
        
        # --- Global Files (30s / 60s) ---
        if self.resolution in ['30s', '60s']:
            # These are single global files, so we just return them if requested.
            # Filter by datatype ('bed' or 'surface').
            url = ETOPO_URLS[self.resolution].get(self.datatype)
            if url:
                self.add_entry_to_results(
                    url=url,
                    dst_fn=f"ETOPO_2022_{self.resolution}_{self.datatype}.tif",
                    data_type='etopo_gtif',
                    agency='NOAA',
                    title=f"ETOPO 2022 Global ({self.resolution})",
                    license='Public Domain'
                )
            else:
                logger.warning(f"Datatype '{self.datatype}' not available for {self.resolution}")
            return self

        # --- Tiled Files (15s) ---
        if self.region is None:
            return []
            
        # Search FRED
        # Filter by DataType (bed/surface/etc) AND Format (gtif/netcdf)
        # The FRED entries have DataType='bed', DataFormat='netcdf'.        
        results = self.fred.search(
            region=self.region,
            filter_func=lambda x: (
                x.get('DataType') == self.datatype and 
                x.get('DataFormat') == self.file_format
            )
        )
        
        for item in results:
            self.add_entry_to_results(
                url=item['DataLink'],
                dst_fn=item['DataLink'].split('/')[-1],
                data_type=f'etopo_{self.file_format}',
                agency='NOAA',
                title=item['Name'],
                license='Public Domain'
            )
            
        return self
