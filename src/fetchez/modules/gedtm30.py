#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
fetchez.modules.gedtm30
~~~~~~~~~~~~~~~~~~~~~~~

Fetch Global 1-Arc-Second Digital Terrain Model (GEDTM30) data 
from OpenLandMap.

:copyright: (c) 2010 - 2026 Regents of the University of Colorado
:license: MIT, see LICENSE for more details.
"""

import os
import csv
import logging
from io import StringIO
from fetchez import core
from fetchez import cli

logger = logging.getLogger(__name__)

# Direct link to the metadata CSV listing all available COGs
GEDTM30_COG_LIST_URL = 'https://raw.githubusercontent.com/openlandmap/GEDTM30/main/metadata/cog_list.csv'

# =============================================================================
# GEDTM30 Module
# =============================================================================
@cli.cli_opts(
    help_text="OpenLandMap GEDTM30 (Global 30m DTM)",
    product="Product Name (e.g., 'Ensemble Digital Terrain Model', 'dtm_downscaled')"
)

class GEDTM30(core.FetchModule):
    """Fetch Global 1-Arc-Second (30m) Digital Terrain Models.
    
    This module queries the OpenLandMap GEDTM30 repository to find 
    Cloud Optimized GeoTIFFs (COGs) matching the requested product name.
    
    Common Products:
      - 'Ensemble Digital Terrain Model' (Default)
      - 'dtm_downscaled'
      - 'dtm_bareearth'
    
    References:
      - https://github.com/openlandmap/GEDTM30
    """
    
    def __init__(self, product: str = 'Ensemble Digital Terrain Model', **kwargs):
        super().__init__(name='gedtm30', **kwargs)
        self.product = product

    def run(self):
        """Run the GEDTM30 fetching logic."""
        
        logger.info("Fetching GEDTM30 file list...")
        req = core.Fetch(GEDTM30_COG_LIST_URL).fetch_req()
        
        if not req or req.status_code != 200:
            logger.error("Failed to retrieve GEDTM30 metadata list.")
            return self

        try:
            f = StringIO(req.text)
            reader = csv.reader(f)
            
            header = next(reader, None)
            
            matches = 0
            for row in reader:
                if not row: continue
                
                # Column 0 is the Product Name
                # Column -1 is the Download URL
                prod_name = row[0]
                url = row[-1]
                
                if self.product.lower() in prod_name.lower():

                    fname = os.path.basename(url)
                    
                    self.add_entry_to_results(
                        url=url,
                        dst_fn=fname,
                        data_type='geotiff',
                        agency='OpenLandMap',
                        title=prod_name
                    )
                    matches += 1
            
            if matches == 0:
                logger.warning(f"No products found matching '{self.product}'.")
            else:
                logger.info(f"Found {matches} files for '{self.product}'.")

        except Exception as e:
            logger.error(f"Error parsing GEDTM30 CSV: {e}")

        return self
