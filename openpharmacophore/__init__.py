"""
OpenPharmacophore
This must be a short description of the project
"""

# Handle versioneer
from ._version import get_versions
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions

__documentation_web__ = 'https://www.uibcdf.org/OpenPharmacophore'
__github_web__ = 'https://github.com/uibcdf/OpenPharmacophore'
__github_issues_web__ = __github_web__ + '/issues'

# Add imports here
from ._pyunitwizard import puw as _puw
from .pharmacophore import Pharmacophore
from .ligand_based import LigandBasedPharmacophore
from .structured_based import StructuredBasedPharmacophore
from .pharmacophoric_point import PharmacophoricPoint
from .screening.screening3D import VirtualScreening3D
from .screening.screening2D import VirtualScreening2D
from .dynophore import Dynophore as Dynophore
from . import demo as demo
