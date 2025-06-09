import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface TimelineEvent {
  year: number;
  description: string;
  image?: string;
}

const App: React.FC = () => {
  const [images, setImages] = useState<string[]>([]);
  const [currentImage, setCurrentImage] = useState<string>('');
  const headShotRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Example timeline events
  const timelineEvents: TimelineEvent[] = [
    { year: 1990, description: "Born" },
    { year: 1995, description: "Started school" },
    { year: 2000, description: "Middle school" },
    { year: 2005, description: "High school" },
    { year: 2010, description: "College" },
    { year: 2015, description: "Career start" },
    { year: 2020, description: "Present day" },
  ];

  useEffect(() => {
    // Fetch processed images from the backend
    const fetchImages = async () => {
      try {
        const response = await axios.get('http://localhost:8000/processed-images');
        setImages(response.data.images);
      } catch (error) {
        console.error('Error fetching images:', error);
      }
    };

    fetchImages();
  }, []);

  useEffect(() => {
    if (!headShotRef.current || !timelineRef.current || images.length === 0) return;

    // Set up GSAP animation
    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: timelineRef.current,
        start: 'top center',
        end: 'bottom center',
        scrub: true,
        onUpdate: (self: any) => {
          // Calculate which image to show based on scroll progress
          const imageIndex = Math.floor(self.progress * images.length);
          const selectedImage = images[Math.min(imageIndex, images.length - 1)];
          setCurrentImage(selectedImage);
        },
      },
    });

    // Animate timeline events
    timeline.from('.timeline-event', {
      opacity: 0,
      y: 20,
      stagger: 0.5,
    });

    return () => {
      timeline.kill();
    };
  }, [images]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await axios.post('http://localhost:8000/upload-images/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // Refresh images after upload
      const response = await axios.get('http://localhost:8000/processed-images');
      setImages(response.data.images);
    } catch (error) {
      console.error('Error uploading images:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8">Age Progression Timeline</h1>
        
        {/* File upload section */}
        <div className="mb-8 text-center">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="bg-blue-500 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-600"
          >
            Upload Photos
          </label>
        </div>

        <div className="flex flex-col md:flex-row gap-8">
          {/* Fixed headshot container */}
          <div
            ref={headShotRef}
            className="md:sticky md:top-8 w-full md:w-1/3 h-[400px] bg-white rounded-lg shadow-lg overflow-hidden"
          >
            {currentImage ? (
              <img
                src={`http://localhost:8000/image/${currentImage}`}
                alt="Current age"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                No image available
              </div>
            )}
          </div>

          {/* Timeline section */}
          <div ref={timelineRef} className="w-full md:w-2/3">
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

              {/* Timeline events */}
              {timelineEvents.map((event) => (
                <div
                  key={event.year}
                  className="timeline-event relative pl-12 pb-8"
                >
                  <div className="absolute left-2 w-4 h-4 bg-blue-500 rounded-full transform -translate-x-1/2"></div>
                  <div className="bg-white rounded-lg p-4 shadow">
                    <h3 className="text-xl font-bold">{event.year}</h3>
                    <p className="text-gray-600">{event.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App; 