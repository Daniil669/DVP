import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import { useState, type ChangeEvent } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useNavigate } from 'react-router';
import { nodeService, sourceService } from '../services/service-instances';

export default function Homepage() {
  const [file, setFile] = useState<File | null>(null);
  const navigate = useNavigate();

  const handleUpload = async (file: File | null) => {
    if (!file) {
      alert('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_now', 'true'); // all values must be strings
    formData.append('connection_id', '1');
    formData.append('eng_id', '');
    formData.append('eng_ids', JSON.stringify([])); // stringify array if backend expects JSON

    for (const [key, value] of formData.entries()) {
      console.log(`${key}:`, value);
    }

    const resp = await sourceService.uploadCSV(formData);
    if (!resp) return;
    handleNodeFetch(resp.dataset_id);
  };

  const handleNodeFetch = async (dataset_id: number) => {
    const rootNode = await nodeService.getRootNode(dataset_id)
    if (rootNode) {
      navigate('/graph', {
        state: {
          nodes: rootNode.root_nodes,
          fileData: dataset_id
        }
      });
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', padding: 4 }}>
      <Paper
        elevation={3}
        sx={{
          padding: 4,
          width: '100%',
          maxWidth: 900,
          backgroundColor: '#f9f9f9',
          borderRadius: 2
        }}
      >
        <Typography variant="h5" gutterBottom sx={{ color: '#333', textAlign: 'center' }}>
          Upload the .CSV file
        </Typography>

        <form>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              flexWrap: 'wrap'
            }}
          >
            <TextField
              type="file"
              variant="outlined"
              inputProps={{ accept: '.csv' }}
              onChange={handleFileChange}
              sx={{ flex: 1, minWidth: 500 }}
            />

            <Button
              variant="contained"
              color="primary"
              onClick={() => handleUpload(file)}
              sx={{
                whiteSpace: 'nowrap',
                height: '56px',
                paddingX: 5
              }}
            >
              Upload
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}
