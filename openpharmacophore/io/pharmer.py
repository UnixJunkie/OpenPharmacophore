from openpharmacophore import _puw
from openpharmacophore.pharmacophoric_point import PharmacophoricPoint
from rdkit import Chem
import pyunitwizard as puw
import json

def from_pharmer(pharmacophore_file, load_mol_sys=False):
    """ Loads a pharmacophore from a pharmer json file

        Parameters
        ----------
        pharmacophore_file: str
            name of the file containing the pharmacophore

        load_mol_sys: bool
            If true loads the molecular system associated to the pharmacophore (Default: False)

        Returns
        -------
        points: list of openpharmacophore.pharmacophoric_elements
            A list of pharmacophoric elements
        
        molecular_system: :obj:`molsysmt.MolSys`
            The molecular system associated with the pharmacophore. If there is no molecular system or
            if load_mol_sys is set to false, None is returned
    """
    points = []
    molecular_system = None
    ligand = None

    if type(pharmacophore_file) == str:
        if pharmacophore_file.endswith('.json'):
            with open(pharmacophore_file, "r") as fff:
                pharmacophore = json.load(fff)
        else:
            raise NotImplementedError

    def get_pharmer_element_properties(element, direction=False):
        center = _puw.quantity([element['x'], element['y'], element['z']], 'angstroms')
        radius = _puw.quantity(element['radius'], 'angstroms')
        if direction:
            direction = [element['svector']['x'], element['svector']['y'], element['svector']['z']]
            return center, radius, direction

        return center, radius

    for pharmer_element in pharmacophore['points']:
        pharmer_feature_name = pharmer_element['name']

        if pharmer_feature_name=='Aromatic':
            center, radius, direction = get_pharmer_element_properties(pharmer_element, direction=True)
            element = PharmacophoricPoint("aromatic ring", center, radius, direction)

        elif pharmer_feature_name=='Hydrophobic':
            center, radius = get_pharmer_element_properties(pharmer_element, direction=False)
            element = PharmacophoricPoint("hydrophobicity", center, radius)

        elif pharmer_feature_name=='HydrogenAcceptor':
            center, radius, direction = get_pharmer_element_properties(pharmer_element, direction=True)
            element = PharmacophoricPoint("hb acceptor" ,center, radius, direction)

        elif pharmer_feature_name=="HydrogenDonor":
            center, radius, direction = get_pharmer_element_properties(pharmer_element, direction=True)
            element = PharmacophoricPoint("hb donor" ,center, radius, direction)

        elif pharmer_feature_name=="PositiveIon":
            center, radius = get_pharmer_element_properties(pharmer_element, direction=False)
            element = PharmacophoricPoint("positive charge", center, radius)
        
        elif pharmer_feature_name=="NegativeIon":
            center, radius = get_pharmer_element_properties(pharmer_element, direction=False)
            element = PharmacophoricPoint("negative charge", center, radius)

        elif pharmer_feature_name=="ExclusionSphere":
            center, radius = get_pharmer_element_properties(pharmer_element, direction=False)
            element = PharmacophoricPoint("excluded volume", center, radius)

        elif pharmer_feature_name=='InclusionSphere':
            center, radius = get_pharmer_element_properties(pharmer_element, direction=False)
            element =PharmacophoricPoint("included volume", center, radius)

        points.append(element)

    if load_mol_sys:
        has_ligand = "ligand" in pharmacophore and pharmacophore["ligand"] != ""
        if has_ligand: 
            ligand = Chem.rdmolfiles.MolFromPDBBlock(pharmacophore["ligand"]) 
        has_receptor = "receptor" in pharmacophore and pharmacophore["receptor"] != ""
        if has_receptor: 
            receptor = Chem.rdmolfiles.MolFromPDBBlock(pharmacophore["receptor"])
            molecular_system = receptor
    
    return points, molecular_system, ligand

def to_pharmer(pharmacophore, file_name):
    """ Save a pharmacophore as a pharmer file (json file)

        Parameters
        ----------

        pharmacophore: obj: openpharmacophore.StructuredBasedPharmacophore or openpharmacophore.Pharmacophore
            Pharmacophore object that will be saved to a file

        file_name: str
            Name of the file that will contain the pharmacophore

        Note
        ----
            Nothing is returned. A new file is written.
    """
    pharmacophore_dict = _pharmer_dict(pharmacophore)
    
    with open(file_name, "w") as outfile:
        json.dump(pharmacophore_dict, outfile)

def _pharmer_dict(pharmacophore):
    """ Returns a Dictionary with the necessary info to construct pharmer pharmacophore. 

        Parameters
        ----------

        pharmacophore: obj: openpharmacophore.StructuredBasedPharmacophore or openpharmacophore.Pharmacophore
            Pharmacophore object wich elements will be used to construct the dictionary

        Returns
        -------
            pharmacophore_dict: dict
                Dictionary with the necessary info to construct a .json pharmer file. 
    """
    pharmer_element_name = { # dictionary to map openpharmacophore feature names to pharmer feature names
        "aromatic ring": "Aromatic",
        "hydrophobicity": "Hydrophobic",
        "hb acceptor": "HydrogenAcceptor",
        "hb donor": "HydrogenDonor",
        "included volume": "InclusionSphere",
        "excluded volume": "ExclusionSphere",
        "positive charge": "PositiveIon",
        "negative charge": "NegativeIon",
    }
    points = []
    for element in pharmacophore.elements:
        point_dict = {}
        temp_center = puw.get_value(element.center, to_unit='angstroms')
        point_dict["name"] = pharmer_element_name[element.feature_name]
        point_dict["svector"] = {}
        if element.has_direction: 
            point_dict["hasvec"] = True
            point_dict["svector"]["x"] = element.direction[0]
            point_dict["svector"]["y"] = element.direction[1] 
            point_dict["svector"]["z"] = element.direction[2]  
        else: 
            point_dict["hasvec"] = False
            point_dict["svector"]["x"] = 1
            point_dict["svector"]["y"] = 0
            point_dict["svector"]["z"] = 0 
        point_dict["x"] = temp_center[0]
        point_dict["y"] = temp_center[1]
        point_dict["z"] = temp_center[2]
        point_dict["radius"] = puw.get_value(element.radius, to_unit='angstroms')
        point_dict["enabled"] = True
        point_dict["vector_on"] = 0
        point_dict["minsize"] = ""
        point_dict["maxsize"] = ""
        point_dict["selected"] = False

        points.append(point_dict)

    pharmacophore_dict = {}
    pharmacophore_dict["points"] = points

    return pharmacophore_dict
    