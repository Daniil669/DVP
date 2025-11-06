import Button from '@mui/material/Button';
import axios from 'axios';
import TextField from '@mui/material/TextField';
import { useState, type ChangeEvent } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useNavigate } from 'react-router';

const connection_id = '1';

export default function Homepage() {
  const [file, setFile] = useState<File | null>(null);
  const navigate = useNavigate();

  const handleUpload = (file: File | null) => {
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

    axios
      .post('http://localhost:8000/api/upload_csv', formData, {
        headers: {
          'x-api-key': 'secret123'
          // no need to manually set Content-Type, axios handles multipart boundaries
        }
      })
      .then(res => {
        console.log('Upload success', res);
        handleNodeFetch(res.data.dataset_id);
      })
      .catch(err => console.error('Upload failed', err.response?.data || err));
  };

  const handleNodeFetch = (dataset_id: number) => {
    axios
      .get(`http://localhost:8000/api/root_node?connection_id=${connection_id}&dataset_id=${dataset_id}`, {
        headers: {
          'x-api-key': 'secret123'
        }
      })
      .then(res => {
        console.log('Root node fetched', res);
        navigate('/graph', {
          state: {
            nodes: res.data.root_nodes,
            fileData: dataset_id
          }
        });
      })
      .catch(err => console.error('Root node fetch error', err));
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
