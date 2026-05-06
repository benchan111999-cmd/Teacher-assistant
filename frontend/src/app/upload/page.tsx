'use client';

import { useState, useEffect, useCallback } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi, documentsApi, topicsApi } from '@/lib/api';
import { Version, Material, Topic } from '@/types/api';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info';

interface ExtractionResult {
  materialId: number;
  fileName: string;
  sectionCount: number;
  topicCount: number;
  topics: Topic[];
  error?: string;
}

const materialStatusVariant = (status: string): BadgeVariant => {
  if (status === 'parsed') return 'success';
  if (status === 'failed') return 'error';
  if (status === 'pending') return 'warning';
  return 'info';
};

const errorMessage = (error: unknown): string => (
  error instanceof Error ? error.message : 'Unknown error'
);

export default function UploadPage() {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [versionStatus, setVersionStatus] = useState<string>('');
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [extractionStatus, setExtractionStatus] = useState<string>('');
  const [extractionResults, setExtractionResults] = useState<ExtractionResult[]>([]);
  const [extracting, setExtracting] = useState(false);
  const [newVersionName, setNewVersionName] = useState('');
  const [newVersionYear, setNewVersionYear] = useState(new Date().getFullYear().toString());
  const [creatingVersion, setCreatingVersion] = useState(false);
  const [pdfPassword, setPdfPassword] = useState('');
  const [pendingDeleteVersionId, setPendingDeleteVersionId] = useState<number | null>(null);
  const [pendingDeleteMaterialId, setPendingDeleteMaterialId] = useState<number | null>(null);

  const loadVersions = useCallback(async () => {
    try {
      const data = await curriculumApi.listVersions();
      setVersions(data);
      setSelectedVersion((current) => current ?? data[0]?.id ?? null);
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  }, []);

  const loadMaterials = useCallback(async (versionId: number) => {
    try {
      const data = await documentsApi.listMaterials(versionId);
      setMaterials(data);
    } catch (error) {
      console.error('Failed to load materials:', error);
    }
  }, []);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  useEffect(() => {
    if (selectedVersion) {
      loadMaterials(selectedVersion);
    }
  }, [selectedVersion, loadMaterials]);

  const handleCreateVersion = async () => {
    const name = newVersionName.trim();
    const year = parseInt(newVersionYear, 10);

    if (!name) {
      setVersionStatus('Enter a curriculum version name first.');
      return;
    }

    if (Number.isNaN(year)) {
      setVersionStatus('Enter a valid year.');
      return;
    }
    
    setCreatingVersion(true);
    setVersionStatus('Creating curriculum version...');

    try {
      const newVersion = await curriculumApi.createVersion(name, year);
      setVersions([...versions, newVersion]);
      setSelectedVersion(newVersion.id);
      setNewVersionName('');
      setPendingDeleteVersionId(null);
      setPendingDeleteMaterialId(null);
      setVersionStatus(`Created version: ${newVersion.name}`);
    } catch (error) {
      setVersionStatus(`Error: ${errorMessage(error)}`);
    } finally {
      setCreatingVersion(false);
    }
  };

  const handleDeleteSelectedVersion = async () => {
    if (!selectedVersion) return;

    if (pendingDeleteVersionId !== selectedVersion) {
      setPendingDeleteVersionId(selectedVersion);
      setVersionStatus('Click Confirm Delete to remove this version and its materials.');
      return;
    }

    try {
      await curriculumApi.deleteVersion(selectedVersion);
      const remaining = versions.filter((version) => version.id !== selectedVersion);
      setVersions(remaining);
      setSelectedVersion(remaining[0]?.id ?? null);
      setMaterials([]);
      setExtractionResults([]);
      setPendingDeleteVersionId(null);
      setPendingDeleteMaterialId(null);
      setVersionStatus('Version deleted.');
    } catch (error) {
      setVersionStatus(`Error: ${errorMessage(error)}`);
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
    setUploadStatus(`Uploading ${files.length} file(s)...`);
    
    try {
      const uploaded: Material[] = [];
      for (const file of files) {
        const material = await documentsApi.uploadMaterial(selectedVersion, file, pdfPassword.trim() || undefined);
        uploaded.push(material);
      }
      setMaterials([...materials, ...uploaded]);
      setFiles([]);
      setPdfPassword('');
      setUploadStatus(`Uploaded ${uploaded.length} file(s)!`);
    } catch (error) {
      setUploadStatus(`Error: ${errorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractAll = async () => {
    if (!selectedVersion || materials.length === 0) return;
    
    setExtracting(true);
    setExtractionStatus('Extracting topics from all materials...');
    setExtractionResults([]);
    
    try {
      let totalTopics = 0;
      const results: ExtractionResult[] = [];
      for (const material of materials) {
        try {
          const sections = await documentsApi.getSections(material.id);
          const sectionIds = sections.map(s => s.id);
          if (sectionIds.length === 0) {
            results.push({
              materialId: material.id,
              fileName: material.file_name,
              sectionCount: 0,
              topicCount: 0,
              topics: [],
              error: 'No parsed sections found.',
            });
            continue;
          }
          const topics = await topicsApi.extractTopics(selectedVersion, sectionIds);
          totalTopics += topics.length;
          results.push({
            materialId: material.id,
            fileName: material.file_name,
            sectionCount: sectionIds.length,
            topicCount: topics.length,
            topics,
          });
        } catch (error) {
          results.push({
            materialId: material.id,
            fileName: material.file_name,
            sectionCount: 0,
            topicCount: 0,
            topics: [],
            error: errorMessage(error),
          });
          break;
        }
      }
      setExtractionResults(results);
      setExtractionStatus(
        results.some((result) => result.error)
          ? 'Topic extraction stopped with an error.'
          : `Extracted ${totalTopics} topics total.`
      );
    } catch (error) {
      setExtractionStatus(`Error: ${errorMessage(error)}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleDeleteMaterial = async (id: number) => {
    if (pendingDeleteMaterialId !== id) {
      setPendingDeleteMaterialId(id);
      setUploadStatus('Click Confirm Delete to remove this material.');
      return;
    }

    try {
      await documentsApi.deleteMaterial(id);
      setMaterials(materials.filter(m => m.id !== id));
      setPendingDeleteMaterialId(null);
      setUploadStatus('Material deleted');
    } catch (error) {
      setUploadStatus(`Error: ${errorMessage(error)}`);
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
              onChange={(e) => {
                setSelectedVersion(parseInt(e.target.value));
                setPendingDeleteVersionId(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.year})
                </option>
              ))}
            </select>
          )}

          {selectedVersion && (
            <div className="mb-4">
              <Button onClick={handleDeleteSelectedVersion} variant="danger">
                {pendingDeleteVersionId === selectedVersion ? 'Confirm Delete' : 'Delete Selected Version'}
              </Button>
            </div>
          )}
          
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_7rem_auto] gap-2">
            <input
              type="text"
              value={newVersionName}
              onChange={(e) => setNewVersionName(e.target.value)}
              placeholder="Version name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <input
              type="number"
              value={newVersionYear}
              onChange={(e) => setNewVersionYear(e.target.value)}
              min="1900"
              max="2100"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <Button onClick={handleCreateVersion} variant="secondary" disabled={creatingVersion}>
              {creatingVersion ? <Spinner size="sm" /> : '+ New Version'}
            </Button>
          </div>

          {versionStatus && (
            <p className="mt-4 text-sm text-gray-600">{versionStatus}</p>
          )}
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

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              PDF password
            </label>
            <input
              type="password"
              value={pdfPassword}
              onChange={(e) => setPdfPassword(e.target.value)}
              placeholder="Optional, used for protected PDFs"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div className="flex gap-2">
            <Button 
              onClick={handleUpload}
              disabled={files.length === 0 || !selectedVersion || loading}
              className="flex-1"
            >
              {loading ? <Spinner /> : `Upload (${files.length})`}
            </Button>
          </div>
          
          {uploadStatus && (
            <p className="mt-4 text-sm text-center text-gray-600">{uploadStatus}</p>
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
                <div key={m.id} className="grid grid-cols-[minmax(0,1fr)_auto_auto] gap-2 items-start p-2 bg-gray-50 rounded">
                  <span className="text-sm break-words" title={m.file_name}>{m.file_name}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant={materialStatusVariant(m.status)}>
                      {m.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDeleteMaterial(m.id)}
                      className="text-red-500 hover:text-red-700 text-xs px-2 py-1 rounded hover:bg-red-50"
                      title="Delete material"
                    >
                      {pendingDeleteMaterialId === m.id ? 'Confirm Delete' : 'Delete'}
                    </button>
                    {pendingDeleteMaterialId === m.id && (
                      <button
                        onClick={() => {
                          setPendingDeleteMaterialId(null);
                          setUploadStatus('');
                        }}
                        className="text-gray-500 hover:text-gray-700 text-xs px-2 py-1 rounded hover:bg-gray-100"
                      >
                        Cancel
                      </button>
                    )}
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

          {extractionStatus && (
            <p className="mt-4 text-sm text-gray-600">{extractionStatus}</p>
          )}

          {extractionResults.length > 0 && (
            <div className="mt-4 space-y-2 max-h-80 overflow-y-auto">
              {extractionResults.map((result) => (
                <div key={result.materialId} className="rounded-lg bg-gray-50 p-3 text-sm">
                  <div className="font-medium text-gray-900 break-words">{result.fileName}</div>
                  <div className="mt-1 text-gray-600">
                    {result.sectionCount} section(s), {result.topicCount} topic(s)
                  </div>
                  {result.error ? (
                    <div className="mt-2 text-red-600">{result.error}</div>
                  ) : result.topics.length > 0 ? (
                    <ul className="mt-2 list-disc pl-5 text-gray-700">
                      {result.topics.map((topic) => (
                        <li key={topic.id}>
                          {topic.name}
                          {topic.subtopics && topic.subtopics.length > 0 && (
                            <span className="text-gray-500"> ({topic.subtopics.length} subtopic(s))</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="mt-2 text-gray-500">No topics returned.</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
