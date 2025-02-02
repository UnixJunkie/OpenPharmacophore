from openpharmacophore._private_tools.exceptions import InvalidFeatureError, InvalidFileError
from openpharmacophore.io import (from_pharmer, from_moe, from_ligandscout, read_pharmagist,
 to_ligandscout, to_moe, to_pharmagist, to_pharmer)
from openpharmacophore.color_palettes import get_color_from_palette_for_feature
import nglview as nv
import pyunitwizard as puw
from rdkit import Chem, Geometry, RDLogger
from rdkit.Chem import ChemicalFeatures
from rdkit.Chem.Pharm3D import Pharmacophore as rdkitPharmacophore
RDLogger.DisableLog('rdApp.*') # Disable rdkit warnings

class Pharmacophore():

    """ Native object for pharmacophores.

    Parent class of LigandBasedPharmacophore, StrucutredBasedPharmacophore and Dynophore
    Openpharmacophore native class to store pharmacophoric models.
    A pharmacophore can be constructed from a list of elements or from a file.

    Parameters
    ----------

    elements : :obj:`list` of :obj:`openpharmacophore.pharmacophoric_point.PharmacophoricPoint`
        List of pharmacophoric elements

    Attributes
    ----------

    elements : :obj:`list` of :obj:`openpharmacophore.pharmacophoric_point.PharmacophoricPoint`
        List of pharmacophoric elements

    n_elements : int
        Number of pharmacophoric elements

    """
    def __init__(self, elements=[]):

        self.elements = elements
        self.n_elements = len(elements)
    
    @classmethod
    def from_file(cls, file_name, **kwargs):
        """
        Class method to load a pharmacohpore from a file.

        Parameters
        ---------
        file_name: str
            Name of the file containing the pharmacophore

        """
        fextension = file_name.split(".")[-1]
        if fextension == "json":
            points, _ , _ = from_pharmer(file_name, False)

        elif fextension == "ph4":
            points = from_moe(file_name)
           
        elif fextension == "pml":
            points = from_ligandscout(file_name)

        elif fextension == "mol2":
            if kwargs:
                ph_index = kwargs["index"]
            else:
                ph_index = 0
            points = read_pharmagist(file_name, pharmacophore_index=ph_index)
        
        else:
            raise InvalidFileError(f"Invalid file type, \"{file_name}\" is not a supported file format")
        
        return cls(elements=points)    
        
    def add_to_NGLView(self, view, palette='openpharmacophore'):

        """Adding the pharmacophore representation to a view (NGLWidget) from NGLView.

        Each pharmacophoric element is added to the NGLWidget as a new component.

        Parameters
        ----------
        view: :obj: `nglview.NGLWidget`
            View as NGLView widget where the representation of the pharmacophore is going to be
            added.
        palette: :obj: `str`, dict
            Color palette name or dictionary. (Default: 'openpharmacophore')

        Note
        ----
        Nothing is returned. The `view` object is modified in place.
        """
        # TODO: Add opacity to spheres
        for i, element in enumerate(self.elements):
            # Add Spheres
            center = puw.get_value(element.center, to_unit="angstroms").tolist()
            radius = puw.get_value(element.radius, to_unit="angstroms")
            feature_color = get_color_from_palette_for_feature(element.feature_name, color_palette=palette)
            label = f"{element.feature_name}_{i}"
            view.shape.add_sphere(center, feature_color, radius, label)
            # Add vectors
            if element.has_direction:
                label = f"{element.feature_name}_vector"
                if element.feature_name == "hb acceptor":
                    end_arrow = puw.get_value(element.center - 2 * radius * puw.quantity(element.direction, "angstroms"), to_unit='angstroms').tolist()
                    view.shape.add_arrow(end_arrow, center, feature_color, 0.2, label)
                else:
                    end_arrow = puw.get_value(element.center + 2 * radius * puw.quantity(element.direction, "angstroms"), to_unit='angstroms').tolist()
                    view.shape.add_arrow(center, end_arrow, feature_color, 0.2, label)
                   
    def show(self, palette='openpharmacophore'):

        """Showing the pharmacophore model together with the molecular system from with it was
        extracted as a new view (NGLWidget) from NGLView.

        Parameters
        ----------
        palette: :obj: `str`, dict
            Color palette name or dictionary. (Default: 'openpharmacophore')

        Returns
        -------
        nglview.NGLWidget
            An nglview.NGLWidget is returned with the 'view' of the pharmacophoric model and the
            molecular system used to elucidate it.

        """

        view = nv.NGLWidget()
        self.add_to_NGLView(view, palette=palette)

        return view

    def add_element(self, pharmacophoric_element):

        """Adding a new element to the pharmacophore.

        Parameters
        ----------
        pharmacophoric_element: :obj: `openpharmacohore.pharmacophoric_elements`
            Native object for pharmacophoric elements of any class defined in the module
            `openpharmacophore.pharmacophoric_elements`

        Returns
        -------

            The pharmacophoric element given as input argument is added to the pharmacophore
            as a new entry of the list `elements`.

        """

        self.elements.append(pharmacophoric_element)
        self.n_elements +=1
    
    def remove_elements(self, element_indices):
        """Remove elements from the pharmacophore.

        Parameters
        ----------
        element_indices: int or list of int
            Indices of the elements to be removed. Can be a list of integers if multiple elements will be
            removed or a single integer to remove one element.

        Returns
        -------
            The pharmacophoric element given as input argument is removed from the pharmacophore.
        """
        if isinstance(element_indices, int):
            self.elements.pop(element_indices)
            self.n_elements -=1
        elif isinstance(element_indices, list):
            new_elements = [element for i, element in enumerate(self.elements) if i not in element_indices]
            self.elements = new_elements
            self.n_elements = len(self.elements)

    def remove_feature(self, feat_type):
        """Remove an especific feature type from the pharmacophore elements list

        Parameters
        ----------
        feat_type: str
            Name or type of the feature to be removed

        Returns
        ------
            The pharmacophoric elements of the feature type given as input argument 
            are removed from the pharmacophore.
        """
        feats = [
            "aromatic ring",
            "hydrophobicity",
            "hb acceptor",
            "hb donor",
            "included volume",
            "excluded volume",
            "positive charge",
            "negative charge",
        ]    
        if feat_type not in feats:
            raise InvalidFeatureError(f"Cannot remove feature. \"{feat_type}\" is not a valid feature type")
        temp_elements = [element for element in self.elements if element.feature_name != feat_type]
        if len(temp_elements) == self.n_elements: # No element was removed
            raise InvalidFeatureError(f"Cannot remove feature. The pharmacophore does not contain any {feat_type}")
        self.elements = temp_elements
        self.n_elements = len(self.elements)
    
    def remove_molecular_system(self):
        """ Set molecular system attribute to None.
        """
        self.molecular_system = None
    
    def set_molecular_system(self, molecular_system):
        """ Update molecular_system attribute.
        """
        self.molecular_system = molecular_system

    def _reset(self):
        """Private method to reset all attributes to default values.

        Note
        ----
        Nothing is returned. All attributes are set to default values.
        """
        self.elements.clear()
        self.n_elements = 0
        self.extractor = None
        self.molecular_system = None

    def to_ligandscout(self, file_name):
        """Method to export the pharmacophore to the ligandscout compatible format.

        Parameters
        ----------
        file_name: str
            Name of file to be written with the ligandscout format of the pharmacophore.

        Note
        ----
        Nothing is returned. A new file is written.

        """
        return to_ligandscout(self, file_name=file_name)

    def to_pharmer(self, file_name):
        """Method to export the pharmacophore to the pharmer compatible format.

        Parameters
        ----------
        file_name: str
            Name of file to be written with the pharmer format of the pharmacophore.

        Note
        ----
            Nothing is returned. A new file is written.

        """
        return to_pharmer(self, file_name=file_name)

    def to_pharmagist(self, file_name):
        """Method to export the pharmacophore to the pharmagist compatible format.

        Parameters
        ----------
        file_name: str
            Name of file to be written with the pharmagist format of the pharmacophore.

        Note
        ----
            Nothing is returned. A new file is written.

        """
        return to_pharmagist(self, file_name=file_name)
    
    def to_moe(self, file_name):
        """Method to export the pharmacophore to the MOE compatible format.

        Parameters
        ----------
        file_name: str
            Name of file to be written with the MOE format of the pharmacophore.

        Note
        ----
            Nothing is returned. A new file is written.

        """
        return to_moe(self, file_name=file_name)
    
    def to_rdkit(self):
        """ Returns an rdkit pharmacophore with the elements from the original
            pharmacophore. rdkit pharmacophores do not store the elements radii,
            so they are returned as well.

            Returns
            -------
            rdkit_pharmacophore: rdkit.Chem.Pharm3D.Pharmacophore
                The rdkit pharmacophore.

            radii: list of float
                List with the radius ina angstroms of each pharmacophoric point.
        """
        rdkit_element_name = { # dictionary to map openpharmacophore feature names to rdkit feature names
        "aromatic ring": "Aromatic",
        "hydrophobicity": "Hydrophobe",
        "hb acceptor": "Acceptor",
        "hb donor": "Donor",
        "positive charge": "PosIonizable",
        "negative charge": "NegIonizable",
        }

        points = []
        radii = []

        for element in self.elements:
            feat_name = rdkit_element_name[element.feature_name]
            center = puw.get_value(element.center, to_unit="angstroms")
            center = Geometry.Point3D(center[0], center[1], center[2])
            points.append(ChemicalFeatures.FreeChemicalFeature(
                feat_name,
                center
            ))
            radius = puw.get_value(element.radius, to_unit="angstroms")
            radii.append(radius)

        rdkit_pharmacophore = rdkitPharmacophore.Pharmacophore(points)
        return rdkit_pharmacophore, radii
    
    def __repr__(self):
        return f"{self.__class__.__name__}(n_elements: {self.n_elements})"

    