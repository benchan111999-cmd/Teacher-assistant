'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi, documentsApi, topicsApi } from '@/lib/api';
import { Version, Material, Section } from '@/types/api';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info';

const materialStatusVariant = (status: string): BadgeVariant => {
  if (status === 'parsed') return 'success';
  if (status === 'failed') return 'error';
  if (status === 'pending') return 'warning';
  return 'info';
};

export default function UploadPage() {
  const router = useRouter();
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    loadVersions();
  }, []);

  useEffect(() => {
    if (selectedVersion) {
      loadMaterials(selectedVersion);
    }
  }, [selectedVersion]);

  const loadVersions = async () => {
    try {
      const data = await curriculumApi.listVersions();
      setVersions(data);
      if (data.length > 0 && !selectedVersion) {
        setSelectedVersion(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const loadMaterials = async (versionId: number) => {
    try {
      const data = await documentsApi.listMaterials(versionId);
      setMaterials(data);
    } catch (error) {
      console.error('Failed to load materials:', error);
    }
  };

  const handleCreateVersion = async () => {
    const name = prompt('Enter curriculum version name:');
    if (!name) return;
    
    const year = parseInt(prompt('Enter year:') || new Date().getFullYear().toString());
    
    try {
      const newVersion = await curriculumApi.createVersion(name, year);
      setVersions([...versions, newVersion]);
      setSelectedVersion(newVersion.id);
    } catch (error) {
      console.error('Failed to create version:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles([...files, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0 || !selectedVersion) return;
    
    setLoading(true);
    setStatus(`Uploading ${files.length} file(s)...`);
    
    try {
      const uploaded: Material[] = [];
      for (const file of files) {
        const material = await documentsApi.uploadMaterial(selectedVersion, file);
        uploaded.push(material);
      }
      setMaterials([...materials, ...uploaded]);
      setFiles([]);
      setStatus(`Uploaded ${uploaded.length} file(s)!`);
    } catch (error: any) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractAll = async () => {
    if (!selectedVersion || materials.length === 0) return;
    
    setExtracting(true);
    setStatus('Extracting topics from all materials...');
    
    try {
      let totalTopics = 0;
      for (const material of materials) {
        const sections = await documentsApi.getSections(material.id);
        const sectionIds = sections.map(s => s.id);
        if (sectionIds.length > 0) {
          const topics = await topicsApi.extractTopics(selectedVersion, sectionIds);
          totalTopics += topics.length;
        }
      }
      setStatus(`Extracted ${totalTopics} topics total!`);
    } catch (error: any) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleDeleteMaterial = async (id: number) => {
    if (!confirm('Delete this material?')) return;
    try {
      await documentsApi.deleteMaterial(id);
      setMaterials(materials.filter(m => m.id !== id));
      setStatus('Material deleted');
    } catch (error: any) {
      setStatus(`Error: ${error.message}`);
    }
  };

  return (
    <Layout title="Upload Materials">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Select Curriculum Version</h3>
          
          {versions.length === 0 ? (
            <p className="text-gray-500 mb-4">No versions yet. Create one first.</p>
          ) : (
            <select
              value={selectedVersion?.toString() || ''}
              onChange={(e) => setSelectedVersion(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.year})
                </option>
              ))}
            </select>
          )}
          
          <Button onClick={handleCreateVersion} variant="secondary">
            + New Version
          </Button>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Upload Files (Multiple)</h3>
          
          <div className="relative border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4 cursor-pointer hover:bg-gray-50 min-h-[100px]">
            <p className="text-gray-500 mb-2">
              {files.length === 0 ? 'Click to select files' : `${files.length} file(s) selected`}
            </p>
            <input
              type="file"
              accept=".pdf,.pptx,.docx,.xlsx"
              multiple
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </div>
          
          {files.length > 0 && (
            <div className="mb-4 max-h-32 overflow-y-auto">
              {files.map((file, index) => (
                <div key={index} className="flex justify-between items-center text-sm bg-gray-50 px-2 py-1 rounded mb-1">
                  <span>{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700 text-xs"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button 
              onClick={handleUpload}
              disabled={files.length === 0 || !selectedVersion || loading}
              className="flex-1"
            >
              {loading ? <Spinner /> : `Upload (${files.length})`}
            </Button>
          </div>
          
          {status && (
            <p className="mt-4 text-sm text-center text-gray-600">{status}</p>
          )}
        </Card>

        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Materials</h3>
            <Badge>{materials.length}</Badge>
          </div>
          
          {materials.length === 0 ? (
            <p className="text-gray-500">No materials uploaded yet.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {materials.map((m) => (
                <div key={m.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="text-sm truncate">{m.file_name}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant={materialStatusVariant(m.status)}>
                      {m.status}
                    </Badge>
                    <button
                      onClick={() => handleDeleteMaterial(m.id)}
                      className="text-red-500 hover:text-red-700 text-xs px-2 py-1 rounded hover:bg-red-50"
                      title="Delete material"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Topic Extraction</h3>
          
          <p className="text-gray-500 mb-4">
            Extract topics from all materials in the current version.
          </p>
          
          <Button 
            onClick={handleExtractAll}
            disabled={materials.length === 0 || extracting}
            className="w-full"
          >
            {extracting ? <Spinner /> : 'Extract All Topics'}
          </Button>
          
          <p className="text-sm text-gray-500 mt-2">
            {materials.length} material(s) ready for extraction.
          </p>
        </Card>
      </div>
    </Layout>
  );
}
