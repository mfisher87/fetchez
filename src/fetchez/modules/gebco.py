#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
fetchez.modules.gebco
~~~~~~~~~~~~~~~~~~~~~

Fetch General Bathymetric Chart of the Oceans (GEBCO) data.
Supports regional subsetting via Cloud Optimized GeoTIFF (COG)
or full global downloads from BODC.

:copyright: (c) 2010 - 2026 Regents of the University of Colorado
:license: MIT, see LICENSE for more details.
"""

import logging
from fetchez.core import FetchModule

logger = logging.getLogger(__name__)

# =============================================================================
# Data Sources
# =============================================================================

# Source Cooperative (Alex Leith) - Cloud Optimized GeoTIFFs
GEBCO_COG_URLS = {
    'grid': 'https://data.source.coop/alexgleith/gebco-2024/GEBCO_2024.tif',
    'tid': 'https://data.source.coop/alexgleith/gebco-2024/GEBCO_2024_TID.tif', 
    'sub_ice': 'https://data.source.coop/alexgleith/gebco-2024/GEBCO_2024_sub_ice_topo.tif'
}

# BODC / Official GEBCO - Global Zipped Downloads
GEBCO_GLOBAL_URLS = {
    'grid': 'https://www.bodc.ac.uk/data/open_download/gebco/gebco_2024/geotiff/',
    'tid': 'https://www.bodc.ac.uk/data/open_download/gebco/gebco_2024_tid/geotiff/',
    'sub_ice': 'https://www.bodc.ac.uk/data/open_download/gebco/gebco_2024_sub_ice_topo/geotiff/'
}

class GEBCO(FetchModule):
    """Fetch GEBCO global bathymetry data.
    
    GEBCO provides a global terrain model at ~15 arc-seconds (~500m).
    
    Layers:
      - grid: Standard bathymetry/topography (Ice Surface). Default.
      - sub_ice: Bedrock elevation (Ice removed).
      - tid: Type Identifier (Source of data per pixel).

    Methods (--source):
      - cog (Default): Uses Cloud Optimized GeoTIFF to download ONLY the 
        requested bounding box (-R). Fastest for regional work.
      - global: Downloads the full global dataset (Zipped GeoTIFF/NetCDF) 
        from the official BODC archive. (~8GB+).
        
    Examples:
      fetchez gebco -R -90/-89/25/26
      fetchez gebco --layer tid --source cog -R ...
      fetchez gebco --layer sub_ice --source global
    """
    
    def __init__(self, layer='grid', source='cog', global_grid=False, **kwargs):
        """
        Args:
            layer (str): 'grid', 'tid', or 'sub_ice'.
            source (str): 'cog' (subset) or 'global' (full download).
            global_grid (bool): Legacy flag, forces source='global'.
        """
        
        super().__init__(name='gebco', **kwargs)
        
        self.layer = layer.lower()
        
        if global_grid:
            self.source = 'global'
        else:
            self.source = source.lower()

        if self.layer not in GEBCO_COG_URLS:
            valid = ", ".join(GEBCO_COG_URLS.keys())
            logger.warning(f"Unknown GEBCO layer '{self.layer}'. Defaulting to 'grid'. Valid: {valid}")
            self.layer = 'grid'

            
    def run(self):
        """Register the files to be fetched."""
        
        if self.source == 'cog':
            self._run_cog()
        elif self.source == 'global':
            self._run_global()
        else:
            logger.error(f"Unknown source method '{self.source}'. Use 'cog' or 'global'.")

            
    def _run_cog(self):
        """Setup for Cloud Optimized GeoTIFF subsetting."""
        
        url = GEBCO_COG_URLS.get(self.layer)
        if not url:
            logger.error(f"No COG URL available for layer '{self.layer}'.")
            return

        # Output filename includes region to avoid overwrites
        if self.region:
            w, e, s, n = self.region
            dst_fn = f"gebco_2024_{self.layer}_{w}_{e}_{s}_{n}.tif"
        else:
            dst_fn = f"gebco_2024_{self.layer}_subset.tif"

        self.add_entry_to_results(
            url=url,
            dst_fn=dst_fn,
            data_type="raster",        
            cog=True
        )

        
    def _run_global(self):
        """Setup for Official Global Download."""
        
        url = GEBCO_GLOBAL_URLS.get(self.layer)
        if not url:
            logger.error(f"No Global URL available for layer '{self.layer}'.")
            return
            
        dst_fn = f"gebco_2024_{self.layer}_global.zip"
        self.add_entry_to_results(
            url=url,
            dst_fn=dst_fn,
            data_type="archive"
        )
