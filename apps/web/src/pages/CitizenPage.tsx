import React, { useState, useEffect } from 'react';
import { Village, Shelter } from '../types';
import { api } from '../services/api';
import { CitizenWarning } from '../components/citizen/CitizenWarning';

export const CitizenPage: React.FC = () => {
  const [villages, setVillages] = useState<Village[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [selectedVillageId, setSelectedVillageId] = useState<any>('bh-01-patna');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    Promise.all([api.getVillages(), api.getShelters()])
      .then(([vData, sData]) => {
        if (isMounted) {
          setVillages(vData);
          setShelters(sData);
          if (vData.length > 0) {
            setSelectedVillageId(vData[0].id);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Error loading citizen view data:', err);
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
        Loading Village Emergency Network...
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: 'transparent', paddingBottom: '40px' }}>
      <CitizenWarning
        villages={villages}
        selectedVillageId={selectedVillageId}
        onSelectVillage={setSelectedVillageId}
        shelters={shelters}
      />
    </div>
  );
};
