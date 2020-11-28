package ca.isupeene.charactersheet.cdk;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.IOException;
import java.util.Objects;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import ca.isupeene.charactersheet.cdk.Parser.ParseException;

/**
 * This class implements most of the work needed to satisfy the requirements for a
 * D&amp;D ContentProvider, assuming your data is organized in an idiomatic way.
 *
 * In particular, the following should be the case:
 * <p><ul>
 * <li>Info and Icons should be organized under the assets directory.
 * <li>The asset paths should match the content_path fields in your content's {@link Model.InfoSource InfoSource} / {@link Model.ImageSource ImageSource}.
 * <li>Icon content paths should specify an image file, while info paths should specify a directory.
 * <li>Info should be organized as a sequence of markdown files under the specified directory.
 * <li>Each markdown file should be titled {index}.{content name}.md, e.g. 01.PRIMAL_INSTINCT.md
 * <li>All other content should be contained in single text proto files under res/raw.
 * </ul><p>
 *
 * You must also implement {@link #ResourceForContentType ResourceForContentType(DlcType)},
 * which returns the resource id of the raw file associated with the specified type.
 * For example, if your custom class is in a file called res/raw/classes.textpb, a call
 * to ResourceForContentType(CLASS) should return R.id.classes. If your content pack does not
 * contain content of a particular type, you should throw a
 * {@link ContentNotSupportedException ContentNotSupportedException}
 * when ResourceForContentType is called for that type.
 */
public abstract class ContentProviderBase extends ContentProvider {
    private static final String TAG = "ContentProviderBase";
    private static final String LEGAL_DLC_TYPES =
            TextUtils.join(", ", Stream.of(DlcType.values()).map(DlcType::Tag).collect(Collectors.toList()));

    /**
     * Throw this from {@link #ResourceForContentType ResourceForContentType} if your
     * content pack does not support the specified {@link DlcType}.
     */
    protected static class ContentNotSupportedException extends Exception { public ContentNotSupportedException() {} }

    /**
     *
     * @param type
     * The type of DLC being requested.  This is never called for ICON or IMAGE types.
     * @return
     * A resource ID corresponding to the raw resource file where the specified content type is defined.
     * E.g. for a file called classes.textpb, you would return the resource id R.raw.classes.
     * @throws ContentNotSupportedException
     * If your content pack does not support the specified content type.
     */
    protected abstract int ResourceForContentType(DlcType type) throws ContentNotSupportedException;

    private byte[] ReadDlcAsBytes(DlcType type) throws IOException, ContentNotSupportedException {
        return type.Parser().apply(getContext().getResources().openRawResource(ResourceForContentType(type))).build().toByteArray();
    }

    /**
     *
     * @param method
     * Specifies the type of content being requested:
     * "backgrounds", "class_spells", "classes", "feats", "items", "spells", "talents", "info", or "image".
     * @param arg
     * For "info" and "image", the content path specified in the {@link Model.InfoSource InfoSource} / {@link Model.ImageSource ImageSource}
     * @param extras
     * Not used
     * @return
     * A bundle containing the result keyed by the provided method name, or an error message keyed by "exception".
     * An empty bundle may also be returned if the requested method is not supported.
     *
     * "image" requests contain the result as a parcelled Bitmap, all others as proto messages serialized to byte[].
     */
    @Override
    public Bundle call(@NonNull String method, @Nullable String arg, @Nullable Bundle extras) {
        Log.i(TAG, "Received call for " + method + " " + arg);
        Bundle result = new Bundle();
        try {
            DlcType dlcType = DlcType.ForTag(method);
            switch (dlcType) {
                case BACKGROUND:
                case CLASS_SPELLS:
                case CLASS:
                case FEAT:
                case ITEM:
                case RACE:
                case SPELL:
                case TALENT:
                    result.putByteArray(method, ReadDlcAsBytes(dlcType));
                    break;
                case INFO:
                    result.putByteArray(method, Utils.GetMultiPageInfoFromAssets(getContext(), Objects.requireNonNull(arg)).toByteArray());
                    break;
                case IMAGE:
                    result.putParcelable(method, Utils.GetBitmapFromAssets(getContext(), Objects.requireNonNull(arg)));
                    break;
            }
        }
        catch (ContentNotSupportedException ex) {
            Log.i(TAG, method + " is not supported by this provider. Returning an empty bundle.");
        }
        catch (EnumConstantNotPresentException ex) {
            String exceptionMessage = method + " is not a valid content method. The valid methods are [" + LEGAL_DLC_TYPES + "]";
            Log.e(TAG, exceptionMessage);
            result.putString(DlcType.EXCEPTION.Tag(), exceptionMessage);
        }
        catch (ParseException ex) {
            Log.e(TAG, "Failed to parse " + method, ex);
            result.putString(DlcType.EXCEPTION.Tag(), ex.getMessage());
        }
        catch (IOException ex) {
            Log.e(TAG, "Error reading content", ex);
            result.putString(DlcType.EXCEPTION.Tag(), ex.getMessage());
        }
        catch (Exception ex) {
            Log.e(TAG, "Unexpected exception", ex);
            result.putString(DlcType.EXCEPTION.Tag(), ex.getMessage());
        }
        return result;
    }

    /**
     * 
     * @param uri
     * Not used
     * @return
     * "application/ca.isupeene.charactersheet"
     */
    @Override
    public String getType(@NonNull Uri uri) {
        return "application/ca.isupeene.charactersheet";
    }

    //region Required Overrides - Unused
    @Override
    public boolean onCreate() {
        return true;
    }

    @Nullable
    @Override
    public Cursor query(@NonNull Uri uri, @Nullable String[] columns, @Nullable String where, @Nullable String[] where_value_substitution, @Nullable String sort_order) {
        return null;
    }

    @Nullable
    @Override
    public Uri insert(@NonNull Uri uri, @Nullable ContentValues contentValues) {
        return null;
    }

    @Override
    public int delete(@NonNull Uri uri, @Nullable String s, @Nullable String[] strings) {
        return 0;
    }

    @Override
    public int update(@NonNull Uri uri, @Nullable ContentValues contentValues, @Nullable String s, @Nullable String[] strings) {
        return 0;
    }
    //endregion
}
