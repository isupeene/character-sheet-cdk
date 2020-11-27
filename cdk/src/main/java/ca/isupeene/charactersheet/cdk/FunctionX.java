package ca.isupeene.charactersheet.cdk;

/**
 * Like {@link java.util.function.Function}, but may throw an exception.
 * @param <T>
 *     Input type
 * @param <R>
 *     Return type
 * @param <X>
 *     The type of Exception that can be thrown.
 */
@FunctionalInterface
public interface FunctionX<T, R, X extends Exception> {
    R apply(T t) throws X;
}
