const express = require('express');
const app = express();
const port = process.env.PORT || 3000;
const Cloudant = require('@cloudant/cloudant');

// Initialize Cloudant connection with IAM authentication
async function dbCloudantConnect() {
    try {
        const cloudant = Cloudant({
            plugins: { iamauth: { iamApiKey: '7mF9N-NipbHTx2ERh8fl5jX34f0SrvRf0pBbKpdRsT-4' } }, // Replace with your IAM API key
            url: 'https://d9fd9fa0-7ce3-416a-894e-47a484082cb0-bluemix.cloudantnosqldb.appdomain.cloud', // Replace with your Cloudant URL
        });

        const db_dealerships = cloudant.use('dealerships');
        const db_reviews = cloudant.use('reviews');

        console.info('Connect success! Connected to DB');
        return {
            dealerships: db_dealerships,
            reviews: db_reviews,
          };
    } catch (err) {
        console.error('Connect failure: ' + err.message + ' for Cloudant DB');
        throw err;
    }
}

let db;

(async () => {
    // db = await dbCloudantConnect();
    db = await dbCloudantConnect();
    db_dealerships = db.dealerships
    db_reviews = db.reviews
    console.log(db_dealerships)
})();

app.use(express.json());

// Define a route to get all dealerships with optional state and ID filters
app.get('/dealerships/get', (req, res) => {
    const { state, id } = req.query;

    // Create a selector object based on query parameters
    const selector = {};
    if (state) {
        selector.state = state;
    }
    
    if (id) {
        selector.id = parseInt(id); // Filter by "id" with a value of 1
    }

    const queryOptions = {
        selector,
        limit: 25, // Limit the number of documents returned to 10
    };

    db_dealerships.find(queryOptions, (err, body) => {
        if (err) {
            console.error('Error fetching dealerships:', err);
            res.status(500).json({ error: 'An error occurred while fetching dealerships.' });
        } else {
            const dealerships = body.docs;
            res.json(dealerships);
        }
    });
})
// app.get('/reviews/get', (req, res) => {
//     const dealerId = req.query;

//     // Create a selector object based on query parameters
//     const selector = {};
//     if (dealerId) {
//         selector.id = parseInt(dealerId);
//     }
    
//     const queryOptions = {
//         selector,
//         limit: 25, // Limit the number of documents returned to 10
//     };
//     // db_reviews.find();
//     db_reviews.find(queryOptions, (err, body) => {
//         if (err) {
//             console.error('Error fetching reviews:', err);
//             res.status(500).json({ error: 'An error occurred while fetching reviews.' });
//         } else {
//             const reviews = body.docs;
//             res.json(reviews);
//         }
//     });
// });
app.get('/reviews/get', async (req, res) => {
    const dealershipId = req.query.dealershipId;
  
    // Create a selector object based on query parameters
    const selector = {};
    if (dealershipId) {
      selector.dealership = parseInt(dealershipId);
    }
  
    const queryOptions = {
      selector,
      limit: 25, // Limit the number of documents returned to 10
    };
  
    const body = await db_reviews.find(queryOptions);
  
    if (body.length === 0) {
      res.status(404).json({ error: 'No reviews found for dealership with ID ' + dealershipId });
    } else {
      const reviews = body.docs;
      res.json(reviews);
    }
  });

  app.post('/reviews', async (req, res) => {
    const review = req.body;
  
    // Validate the review
    if (!review.dealership || !review.car_make || !review.review) {
      res.status(400).json({ error: 'Invalid review' });
      return;
    }
  
    // Save the review to the database
    try {
      await db_reviews.insert(review);
      res.status(201).json({ message: 'Review created successfully' });
    } catch (err) {
      console.error('Error saving review:', err);
      res.status(500).json({ error: 'An error occurred while saving the review' });
    }
  });
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});