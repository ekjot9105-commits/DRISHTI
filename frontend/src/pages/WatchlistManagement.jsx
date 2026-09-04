import { useState, useEffect } from 'react';
import { getFaces, addFace, deleteFace, getPlates, addPlate, deletePlate } from '../services/api';

export default function WatchlistManagement() {
  const [activeTab, setActiveTab] = useState('faces');
  
  // Data state
  const [faces, setFaces] = useState([]);
  const [plates, setPlates] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [faceName, setFaceName] = useState('');
  const [faceDesc, setFaceDesc] = useState('');
  const [faceImage, setFaceImage] = useState(null);
  const [isAuthorized, setIsAuthorized] = useState(false);
  
  const [plateNumber, setPlateNumber] = useState('');
  const [vehicleDesc, setVehicleDesc] = useState('');
  const [ownerName, setOwnerName] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const f = await getFaces();
      setFaces(f);
      const p = await getPlates();
      setPlates(p);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleAddFace = async (e) => {
    e.preventDefault();
    if (!faceImage || !faceName) return;
    
    try {
      await addFace(faceName, faceDesc, faceImage, isAuthorized);
      setFaceName('');
      setFaceDesc('');
      setFaceImage(null);
      setIsAuthorized(false);
      e.target.reset();
      loadData();
    } catch (err) {
      alert("Error adding face: " + err.message);
    }
  };

  const handleAddPlate = async (e) => {
    e.preventDefault();
    if (!plateNumber) return;
    
    try {
      await addPlate(plateNumber, vehicleDesc, ownerName);
      setPlateNumber('');
      setVehicleDesc('');
      setOwnerName('');
      loadData();
    } catch (err) {
      alert("Error adding plate: " + err.message);
    }
  };

  const handleDeleteFace = async (id) => {
    try {
      await deleteFace(id);
      loadData();
    } catch (err) {
      alert("Error deleting face");
    }
  };

  const handleDeletePlate = async (id) => {
    try {
      await deletePlate(id);
      loadData();
    } catch (err) {
      alert("Error deleting plate");
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-primary mb-2">Watchlist Management</h1>
          <p className="text-on-surface-variant">Add known targets to trigger critical alerts upon AI detection.</p>
        </div>
        <div className="flex border border-outline-variant/30 rounded-sm overflow-hidden font-label-caps text-sm">
          <button 
            className={`px-4 py-2 flex items-center ${activeTab === 'faces' ? 'bg-primary text-on-primary' : 'bg-surface text-on-surface-variant hover:bg-surface-variant'}`}
            onClick={() => setActiveTab('faces')}
          >
            <span className="material-symbols-outlined text-[16px] mr-2">face</span>
            Persons
          </button>
          <button 
            className={`px-4 py-2 flex items-center ${activeTab === 'plates' ? 'bg-primary text-on-primary' : 'bg-surface text-on-surface-variant hover:bg-surface-variant'}`}
            onClick={() => setActiveTab('plates')}
          >
            <span className="material-symbols-outlined text-[16px] mr-2">directions_car</span>
            Vehicles
          </button>
        </div>
      </div>

      <div className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-sm flex">
        {/* Sidebar Form */}
        <div className="w-1/3 border-r border-outline-variant/30 p-6 flex flex-col bg-surface-dim/30">
          <h2 className="text-primary font-label-caps mb-6 flex items-center tracking-widest">
            <span className="material-symbols-outlined text-[16px] mr-2">add_circle</span>
            {activeTab === 'faces' ? 'ADD TARGET PERSON' : 'ADD SUSPECT VEHICLE'}
          </h2>
          
          {activeTab === 'faces' ? (
            <form onSubmit={handleAddFace} className="space-y-4 flex-1 flex flex-col">
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">Target Name *</label>
                <input 
                  type="text" 
                  value={faceName}
                  onChange={(e) => setFaceName(e.target.value)}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">Clear Facial Photo *</label>
                <input 
                  type="file" 
                  accept="image/*"
                  onChange={(e) => setFaceImage(e.target.files[0])}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none file:mr-4 file:py-1 file:px-3 file:rounded-sm file:border-0 file:text-xs file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">Notes / Description</label>
                <textarea 
                  value={faceDesc}
                  onChange={(e) => setFaceDesc(e.target.value)}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none h-24 resize-none"
                />
              </div>
              
              <div className="flex items-center mt-2">
                <input 
                  type="checkbox" 
                  id="isAuthorized"
                  checked={isAuthorized}
                  onChange={(e) => setIsAuthorized(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="isAuthorized" className="text-xs font-label-caps text-on-surface-variant">Mark as Authorized Personnel (Suppresses Alerts)</label>
              </div>
<div className="mt-auto">
                <button type="submit" className="w-full bg-primary text-on-primary py-2 rounded-sm font-label-caps text-xs tracking-wider flex items-center justify-center hover:bg-primary/90 transition-colors">
                  <span className="material-symbols-outlined text-[16px] mr-2">person_add</span>
                  SAVE TO WATCHLIST
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleAddPlate} className="space-y-4 flex-1 flex flex-col">
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">License Plate Number *</label>
                <input 
                  type="text" 
                  value={plateNumber}
                  onChange={(e) => setPlateNumber(e.target.value)}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none uppercase font-data-display tracking-widest"
                  placeholder="e.g. AB12CD3456"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">Owner Name</label>
                <input 
                  type="text" 
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-label-caps text-on-surface-variant mb-1">Vehicle Description</label>
                <textarea 
                  value={vehicleDesc}
                  onChange={(e) => setVehicleDesc(e.target.value)}
                  className="w-full bg-surface border border-outline-variant/50 text-on-surface rounded-sm p-2 text-sm focus:border-primary focus:outline-none h-24 resize-none"
                  placeholder="e.g. Black SUV"
                />
              </div>
              <div className="mt-auto">
                <button type="submit" className="w-full bg-primary text-on-primary py-2 rounded-sm font-label-caps text-xs tracking-wider flex items-center justify-center hover:bg-primary/90 transition-colors">
                  <span className="material-symbols-outlined text-[16px] mr-2">playlist_add</span>
                  SAVE TO WATCHLIST
                </button>
              </div>
            </form>
          )}
        </div>

        {/* List View */}
        <div className="w-2/3 p-6 overflow-y-auto">
          {loading ? (
             <div className="flex items-center justify-center h-full text-primary">
                <span className="material-symbols-outlined animate-spin mr-2">sync</span> Loading Database...
             </div>
          ) : activeTab === 'faces' ? (
             <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                {faces.length === 0 && <p className="text-on-surface-variant text-sm col-span-3">No persons currently on watchlist.</p>}
                {faces.map(face => (
                  <div key={face.id} className="border border-outline-variant/30 rounded-sm p-3 bg-surface group relative">
                    <button onClick={() => handleDeleteFace(face.id)} className="absolute top-2 right-2 text-error opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                    <div className="aspect-square bg-surface-dim mb-3 rounded-sm overflow-hidden border border-outline-variant/20">
                      <img src={`http://localhost:8000/data/faces/${face.image_path.split(/[\/\\]/).pop()}`} className="w-full h-full object-cover" alt={face.name} />
                    </div>
                    <h3 className="text-primary font-label-caps text-sm truncate">{face.name}</h3>
                    <p className="text-on-surface-variant text-xs mt-1 line-clamp-2">{face.description || 'No description'}</p>
                  </div>
                ))}
             </div>
          ) : (
             <div className="space-y-3">
                {plates.length === 0 && <p className="text-on-surface-variant text-sm">No vehicles currently on watchlist.</p>}
                {plates.map(plate => (
                  <div key={plate.id} className="border border-error/30 rounded-sm p-4 bg-error/5 flex justify-between items-center group">
                    <div>
                      <div className="flex items-center space-x-3 mb-1">
                        <span className="font-data-display text-lg tracking-widest text-error px-2 py-0.5 border border-error/50 rounded-sm bg-error/10">{plate.plate_number}</span>
                        <span className="text-on-surface text-sm font-semibold">{plate.ownerName || 'Unknown Owner'}</span>
                      </div>
                      <p className="text-on-surface-variant text-xs">{plate.vehicle_description || 'No description provided'}</p>
                    </div>
                    <button onClick={() => handleDeletePlate(plate.id)} className="text-error opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-error/10 rounded-full">
                      <span className="material-symbols-outlined">delete</span>
                    </button>
                  </div>
                ))}
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
