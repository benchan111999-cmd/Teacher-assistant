'use client';

import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi } from '@/lib/api';
import { Version, Outline } from '@/types/api';

export default function CurriculumPage() {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVersions();
  }, []);

  useEffect(() => {
    if (selectedVersion) {
      loadOutlines();
    }
  }, [selectedVersion]);

  const loadVersions = async () => {
    try {
      const data = await curriculumApi.listVersions();
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const loadOutlines = async () => {
    if (!selectedVersion) return;
    setLoading(true);
    try {
      const data = await curriculumApi.listOutlines(selectedVersion);
      setOutlines(data);
    } catch (error) {
      console.error('Failed to load outlines:', error);
      setOutlines([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOutline = async () => {
    if (!selectedVersion) return;
    
    if (!confirm('Generate AI-suggested outline?')) return;
    
    setLoading(true);
    try {
      const data = await curriculumApi.suggestOutline(selectedVersion);
      const outline = await curriculumApi.createOutline(selectedVersion, data.items || []);
      setOutlines([...outlines, outline]);
    } catch (error) {
      console.error('Failed to create outline:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDiff = async () => {
    const versionAId = parseInt(prompt('Enter first version ID:') || '0');
    const versionBId = parseInt(prompt('Enter second version ID:') || '0');
    
    if (!versionAId || !versionBId) return;
    
    try {
      const diff = await curriculumApi.diffVersions(versionAId, versionBId);
      alert(
        `Common: ${diff.common.length}\n` +
        `Unique to A: ${diff.unique_to_version_a.length}\n` +
        `Unique to B: ${diff.unique_to_version_b.length}`
      );
    } catch (error) {
      console.error('Failed to diff versions:', error);
    }
  };

  const parseItems = (itemsStr?: string): any[] => {
    if (!itemsStr) return [];
    try {
      return JSON.parse(itemsStr);
    } catch {
      return [];
    }
  };

  return (
    <Layout title="Curriculum">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">Versions</h3>
          
          {versions.length === 0 ? (
            <p className="text-gray-500">No versions yet.</p>
          ) : (
            <select
              value={selectedVersion?.toString() || ''}
              onChange={(e) => setSelectedVersion(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.year})
                </option>
              ))}
            </select>
          )}
          
          <Button onClick={handleCreateOutline} variant="secondary" className="mt-4 w-full">
            + AI Suggest Outline
          </Button>
          
          <Button onClick={handleDiff} variant="danger" className="mt-2 w-full">
            Compare Versions
          </Button>
        </Card>

        <Card className="p-6 col-span-2">
          <h3 className="text-lg font-medium mb-4">Outline</h3>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : (
            <div>
              {outlines.map((outline) => (
                <div key={outline.id}>
                  <p className="text-sm text-gray-500 mb-2">
                    {parseItems(outline.items).length} items
                  </p>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {parseItems(outline.items).map((item: any, index: number) => (
                      <div
                        key={index}
                        className="p-3 bg-gray-50 rounded-lg flex items-center gap-2"
                      >
                        <Badge variant={item.type === 'topic' ? 'success' : 'info'}>
                          {item.type || 'item'}
                        </Badge>
                        <span>{item.title || item.topic_id}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
