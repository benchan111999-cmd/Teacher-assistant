'use client';

import { useState, useEffect, useCallback } from 'react';
import Layout from '@/components/Layout';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { curriculumApi } from '@/lib/api';
import { CurriculumDiff, Outline, OutlineItem, Version } from '@/types/api';

export default function CurriculumPage() {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [diffVersionAId, setDiffVersionAId] = useState<number | null>(null);
  const [diffVersionBId, setDiffVersionBId] = useState<number | null>(null);
  const [diffResult, setDiffResult] = useState<CurriculumDiff | null>(null);

  const loadVersions = useCallback(async () => {
    try {
      const data = await curriculumApi.listVersions();
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0].id);
        setDiffVersionAId(data[0].id);
        setDiffVersionBId(data[1]?.id ?? data[0].id);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  }, []);

  const loadOutlines = useCallback(async () => {
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
  }, [selectedVersion]);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  useEffect(() => {
    if (selectedVersion) {
      loadOutlines();
    }
  }, [selectedVersion, loadOutlines]);

  const handleCreateOutline = async () => {
    if (!selectedVersion) return;

    setLoading(true);
    setStatus('Generating AI-suggested outline...');
    try {
      const data = await curriculumApi.suggestOutline(selectedVersion);
      const outline = await curriculumApi.createOutline(selectedVersion, data.items || []);
      setOutlines([...outlines, outline]);
      setStatus('Outline created.');
    } catch (error) {
      console.error('Failed to create outline:', error);
      setStatus('Failed to create outline.');
    } finally {
      setLoading(false);
    }
  };

  const handleDiff = async () => {
    if (!diffVersionAId || !diffVersionBId) {
      setStatus('Select two versions to compare.');
      return;
    }

    try {
      const diff = await curriculumApi.diffVersions(diffVersionAId, diffVersionBId);
      setDiffResult(diff);
      setStatus('Version comparison complete.');
    } catch (error) {
      console.error('Failed to diff versions:', error);
      setStatus('Failed to compare versions.');
    }
  };

  const parseItems = (itemsStr?: string): OutlineItem[] => {
    if (!itemsStr) return [];
    try {
      const parsed = JSON.parse(itemsStr);
      return Array.isArray(parsed) ? parsed : [];
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

          <div className="mt-6 space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Compare Versions</h4>
            <select
              value={diffVersionAId?.toString() || ''}
              onChange={(e) => setDiffVersionAId(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.year})
                </option>
              ))}
            </select>
            <select
              value={diffVersionBId?.toString() || ''}
              onChange={(e) => setDiffVersionBId(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.year})
                </option>
              ))}
            </select>
          </div>

          <Button onClick={handleDiff} variant="danger" className="mt-2 w-full">
            Compare Versions
          </Button>

          {status && (
            <p className="mt-4 text-sm text-gray-600">{status}</p>
          )}

          {diffResult && (
            <div className="mt-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
              <div>Common: {diffResult.common.length}</div>
              <div>Unique to A: {diffResult.unique_to_version_a.length}</div>
              <div>Unique to B: {diffResult.unique_to_version_b.length}</div>
            </div>
          )}
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
                    {parseItems(outline.items).map((item, index) => (
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
