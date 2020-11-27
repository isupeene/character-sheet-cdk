package ca.isupeene.charactersheet.cdk;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.text.TextUtils;

import androidx.annotation.NonNull;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import ca.isupeene.charactersheet.cdk.Model.InfoPage;
import ca.isupeene.charactersheet.cdk.Model.MultiPageInfo;

/**
 * Functions to assist in retrieving content from your pack's assets directory.
 */
public abstract class Utils {
    /**
     * Read all text from an {@link InputStream} and return the result as a String.
     * @param inputStream
     * The input data to read.
     * @return
     * A String containing all the data from the InputStream
     * @throws IOException
     * If an error occurs while reading the stream.
     */
    public static @NonNull String ReadAll(@NonNull InputStream inputStream) throws IOException {
        try (BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream))) {
            List<String> lines = new ArrayList<>();

            String line;
            while ((line = bufferedReader.readLine()) != null) {
                lines.add(line);
            }

            return TextUtils.join("\n", lines);
        }
    }

    /**
     * Gets a {@link MultiPageInfo} object from your content pack's asset directory at the specified path.
     * @param context
     * {@link Context} object required to access assets.
     * @param assetPath
     * The directory under which the info files are located, relative to your content pack's "assets" directory.
     * @return
     * A {@link MultiPageInfo} with one {@link InfoPage} per file in the specified directory.
     * @throws IOException
     * If there is an error reading the file.
     */
    public static @NonNull MultiPageInfo GetMultiPageInfoFromAssets(@NonNull Context context, @NonNull String assetPath) throws IOException {
        MultiPageInfo.Builder multiPageBuilder = MultiPageInfo.newBuilder();
        for (String filename : context.getAssets().list(assetPath)) {
            String[] nameParts = filename.split("\\.");
            multiPageBuilder.addPage
                    (InfoPage.newBuilder()
                            .setTitle(nameParts[1])
                            .setContent(ReadAll(context.getAssets().open(assetPath + '/' + filename))));
        }
        return multiPageBuilder.build();
    }

    /**
     * Gets a {@link Bitmap} from your content pack's asset directory at the specified path.
     * @param context
     * {@link Context} object required to access assets.
     * @param assetPath
     * The file containing the image, relative to your content pack's "assets" directory.
     * @return
     * A {@link Bitmap} containing the image in the specified file.
     * @throws IOException
     * If there is an error reading the file.
     */
    public static @NonNull Bitmap GetBitmapFromAssets(@NonNull Context context, @NonNull String assetPath) throws IOException {
        return BitmapFactory.decodeStream(context.getAssets().open(assetPath));
    }
}
